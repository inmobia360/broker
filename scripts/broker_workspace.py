#!/usr/bin/env python3
"""Create and validate isolated BROKER agency workspaces."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import re
import shutil
import stat
import subprocess
import sys
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    tomllib = None


REPO_ROOT = Path(__file__).resolve().parents[1]
MAX_ATTACHMENT_BYTES = 100 * 1024 * 1024
ALLOWED_ATTACHMENT_SUFFIXES = {
    ".csv", ".docx", ".heic", ".jpeg", ".jpg", ".md", ".pdf", ".png",
    ".tif", ".tiff", ".txt", ".webp", ".xls", ".xlsx", ".zip",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
    if not slug:
        raise ValueError("El nombre de la agencia no produce un slug valido.")
    return slug[:64].rstrip("-")


def require_slug(value: str) -> str:
    normalized = slugify(value)
    if normalized != value:
        raise ValueError(f"Identificador no seguro. Usa el slug normalizado: {normalized}")
    return value


def require_case_id(value: str) -> str:
    if not re.fullmatch(r"CASE-[A-Z0-9-]{6,40}", value):
        raise ValueError("case_id no cumple el formato seguro CASE-...")
    return value


def require_operation_type(value: str) -> str:
    if value == "unknown":
        return value
    return require_slug(value)


def require_jurisdiction(value: str) -> str:
    if not re.fullmatch(r"unknown|es(?:-[a-z0-9]{2,12})?", value):
        raise ValueError("jurisdiction debe ser unknown, es o es-<territorio>.")
    return value


def yaml_text(value: str) -> str:
    """Return user text safe for a quoted, single-line YAML scalar."""
    return re.sub(r"\s+", " ", value).strip().replace("\\", "\\\\").replace('"', "'")


def replace_text_tree(path: Path, replacements: dict[str, str]) -> None:
    for file_path in path.rglob("*"):
        if not file_path.is_file():
            continue
        text = file_path.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        file_path.write_text(text, encoding="utf-8", newline="\n")


def create_agency(root: Path, display_name: str, slug: str | None = None) -> Path:
    agency_slug = slugify(slug or display_name)
    if slug is not None and agency_slug != slug:
        raise ValueError(f"El slug debe estar normalizado. Sugerencia: {agency_slug}")

    template = root / "knowledge" / "agencies" / "_template"
    destination = root / "knowledge" / "agencies" / agency_slug
    if not template.is_dir():
        raise FileNotFoundError(f"No existe la plantilla: {template}")

    if destination.exists():
        agency_file = destination / "agency.md"
        existing = agency_file.read_text(encoding="utf-8") if agency_file.exists() else ""
        expected = f'display_name: "{yaml_text(display_name)}"'
        if expected not in existing:
            raise FileExistsError(
                f"Ya existe {agency_slug}, pero no coincide con {display_name!r}. "
                "Confirma si se trata de la misma agencia."
            )
        return destination

    shutil.copytree(template, destination)
    now = utc_now()
    safe_display_name = yaml_text(display_name)
    replacements = {
        "agency-slug": agency_slug,
        'display_name: ""': f'display_name: "{safe_display_name}"',
        "AGY-YYYY-NNNN": f"AGY-{now:%Y}-{uuid.uuid4().hex[:6].upper()}",
        "created_at: YYYY-MM-DD": f"created_at: {now:%Y-%m-%d}",
    }
    replace_text_tree(destination, replacements)
    (root / "workspace" / "agencies" / agency_slug / "cases").mkdir(
        parents=True, exist_ok=True
    )
    return destination


def next_case_id(root: Path, agency_slug: str) -> str:
    prefix = f"CASE-{utc_now():%Y%m%d}"
    cases_dir = root / "workspace" / "agencies" / agency_slug / "cases"
    existing = {p.name for p in cases_dir.glob(f"{prefix}-*") if p.is_dir()}
    for number in range(1, 10000):
        candidate = f"{prefix}-{number:04d}"
        if candidate not in existing:
            return candidate
    raise RuntimeError("No hay identificadores de expediente disponibles para hoy.")


def create_case(
    root: Path,
    agency_slug: str,
    objective: str,
    operation_type: str = "unknown",
    jurisdiction: str = "unknown",
    case_id: str | None = None,
) -> Path:
    require_slug(agency_slug)
    require_operation_type(operation_type)
    require_jurisdiction(jurisdiction)
    agency_path = root / "knowledge" / "agencies" / agency_slug
    if not agency_path.is_dir():
        raise FileNotFoundError(
            f"La agencia {agency_slug!r} no existe. Creala antes de abrir el expediente."
        )
    template = root / "workspace" / "agencies" / "_template" / "cases" / "CASE-TEMPLATE"
    identifier = case_id or next_case_id(root, agency_slug)
    require_case_id(identifier)
    destination = root / "workspace" / "agencies" / agency_slug / "cases" / identifier
    if destination.exists():
        raise FileExistsError(f"El expediente ya existe: {identifier}")
    shutil.copytree(template, destination)
    now = utc_now()
    replacements = {
        "CASE-YYYY-NNNN": identifier,
        "agency-slug": agency_slug,
        "YYYY-MM-DDTHH:MM:SSZ": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "operation_type: unknown": f"operation_type: {operation_type}",
        "jurisdiction: unknown": f"jurisdiction: {jurisdiction}",
        "# Objetivo\n": f"# Objetivo\n\n{objective.strip()}\n",
    }
    replace_text_tree(destination, replacements)
    (destination / "sources").mkdir(exist_ok=True)
    (destination / "deliverables").mkdir(exist_ok=True)
    return destination


def safe_filename(value: str) -> str:
    stem = slugify(Path(value).stem)[:48]
    suffix = re.sub(r"[^a-zA-Z0-9.]", "", Path(value).suffix.lower())[:12]
    return f"{stem}{suffix}"


def is_reparse_point(path: Path) -> bool:
    attributes = getattr(path.stat(), "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return path.is_symlink() or bool(attributes & reparse_flag)


def sha256_stream(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sanitize_url(value: str) -> tuple[str, bool]:
    if re.search(r"[\x00-\x20]", value):
        raise ValueError("La URL contiene caracteres de control o espacios.")
    parts = urlsplit(value)
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise ValueError("La URL debe ser http(s) y tener un host valido.")
    if parts.username or parts.password:
        raise ValueError("No se admiten credenciales incrustadas en la URL.")
    try:
        port = parts.port
    except ValueError as exc:
        raise ValueError("La URL contiene un puerto invalido.") from exc
    if port not in (None, 80, 443):
        raise ValueError("No se admiten puertos no estandar en fuentes URL.")
    hostname = parts.hostname.lower().rstrip(".")
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
        raise ValueError("No se admiten destinos locales.")
    try:
        address = ipaddress.ip_address(hostname.strip("[]"))
    except ValueError:
        address = None
    if address and not address.is_global:
        raise ValueError("No se admiten direcciones IP privadas o reservadas.")
    redacted = urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, "", ""))
    return redacted, bool(parts.query or parts.fragment)


def register_source(
    root: Path,
    agency_slug: str,
    case_id: str,
    objective: str,
    source_path: str | None,
    url: str | None,
    classification: str,
) -> Path:
    require_slug(agency_slug)
    require_case_id(case_id)
    if bool(source_path) == bool(url):
        raise ValueError("Indica exactamente una fuente: --file o --url.")
    case_dir = root / "workspace" / "agencies" / agency_slug / "cases" / case_id
    if not case_dir.is_dir():
        raise FileNotFoundError(f"No existe el expediente: {case_dir}")
    source_id = f"SRC-{utc_now():%Y}-{uuid.uuid4().hex[:8].upper()}"
    received = utc_now().strftime("%Y-%m-%d")
    source_type = "url"
    sha256 = "unknown"

    if source_path:
        original = Path(source_path).expanduser().resolve()
        if not original.is_file():
            raise FileNotFoundError(f"No existe el archivo: {original}")
        if is_reparse_point(original):
            raise ValueError("No se admiten enlaces simbolicos o puntos de reanalisis.")
        if original.suffix.lower() not in ALLOWED_ATTACHMENT_SUFFIXES:
            raise ValueError(f"Tipo de archivo no admitido: {original.suffix or '(sin extension)'}")
        if original.stat().st_size > MAX_ATTACHMENT_BYTES:
            raise ValueError("El adjunto supera el limite de 100 MiB.")
        source_type = "attachment"
        private_dir = root / "inbox" / agency_slug / case_id
        private_dir.mkdir(parents=True, exist_ok=True)
        stored = private_dir / f"{source_id.lower()}-{safe_filename(original.name)}"
        shutil.copy2(original, stored)
        sha256 = sha256_stream(stored)
        reference = str(stored.relative_to(root)).replace("\\", "/")
        title = yaml_text(original.name)
    else:
        reference, has_private_parts = sanitize_url(url or "")
        if has_private_parts:
            private_dir = root / "private" / agency_slug / case_id
            private_dir.mkdir(parents=True, exist_ok=True)
            (private_dir / f"{source_id.lower()}.url").write_text(
                url or "", encoding="utf-8", newline="\n"
            )
        title = reference

    record = case_dir / "sources" / f"{source_id.lower()}.md"
    record.write_text(
        f'''---
source_id: {source_id}
agency: {agency_slug}
case_id: {case_id}
source_type: {source_type}
title: "{title}"
original_reference: "{reference}"
received_at: {received}
retrieved_at: null
objective: "{yaml_text(objective)}"
classification: {classification}
authorization_status: pending
authorized_by: null
authorized_at: null
authorization_scope: resource-only
contains_personal_data: unknown
data_controller: unknown
legal_basis: unknown
retention_until: unknown
jurisdiction: unknown
effective_date: unknown
status: draft
reviewed_by: []
sha256: {sha256}
---

# Resumen fiel

Pendiente de extraccion y revision para el objetivo declarado.

# Evidencias y localizadores

# Limitaciones

# Conocimiento candidato
''',
        encoding="utf-8",
        newline="\n",
    )
    return record


def close_case(root: Path, agency_slug: str, case_id: str) -> Path:
    require_slug(agency_slug)
    require_case_id(case_id)
    case_dir = root / "workspace" / "agencies" / agency_slug / "cases" / case_id
    quality = case_dir / "quality.md"
    closure = case_dir / "closure.md"
    request = case_dir / "request.md"
    if not all(path.is_file() for path in (quality, closure, request)):
        raise FileNotFoundError(f"Expediente incompleto: {case_dir}")
    quality_text = quality.read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n", quality_text, flags=re.DOTALL)
    if not match:
        raise PermissionError("quality.md no tiene front matter valido.")
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    required_approval = {
        "decision": "approved",
        "reviewed_by": "control_calidad",
        "evidence_complete": "true",
        "privacy_checked": "true",
        "authorizations_checked": "true",
    }
    if any(fields.get(key) != value for key, value in required_approval.items()):
        raise PermissionError("CONTROL DE CALIDAD no ha completado todas las puertas.")
    if fields.get("reviewed_at") in {None, "", "null"}:
        raise PermissionError("La aprobacion de CALIDAD carece de fecha.")
    if not fields.get("approval_id", "").startswith("QA-"):
        raise PermissionError("La aprobacion de CALIDAD carece de identificador.")
    closed_at = utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")
    closure_text = closure.read_text(encoding="utf-8")
    closure_text = re.sub(r"(?m)^status:\s*\S+", "status: closed", closure_text, count=1)
    closure_text = re.sub(r"(?m)^closed_at:\s*\S+", f"closed_at: {closed_at}", closure_text, count=1)
    closure.write_text(closure_text, encoding="utf-8", newline="\n")
    request_text = request.read_text(encoding="utf-8")
    request_text = re.sub(r"(?m)^status:\s*\S+", "status: closed", request_text, count=1)
    request.write_text(request_text, encoding="utf-8", newline="\n")
    return closure


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    required = [
        "AGENTS.md",
        ".codex/config.toml",
        "skills/broker-inmobiliario/SKILL.md",
        "skills/broker-inmobiliario/references/routing.md",
        "skills/broker-inmobiliario/references/ingestion.md",
        "skills/broker-inmobiliario/references/knowledge-governance.md",
        "skills/broker-inmobiliario/references/quality-gates.md",
        "knowledge/INDEX.md",
        "knowledge/templates/source.md",
        "knowledge/templates/knowledge-proposal.md",
        "knowledge/proposals/README.md",
        "knowledge/agencies/_template/agency.md",
    ]
    for relative in required:
        if not (root / relative).is_file():
            errors.append(f"Falta {relative}")

    agents = sorted((root / ".codex" / "agents").glob("*.toml"))
    if len(agents) < 10:
        errors.append(f"Se esperaban al menos 10 agentes y hay {len(agents)}")
    if tomllib is None:
        errors.append("Python 3.11+ es necesario para validar TOML")
    else:
        names: set[str] = set()
        for path in agents:
            try:
                data = tomllib.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001 - validator reports all errors
                errors.append(f"TOML invalido {path.name}: {exc}")
                continue
            for key in ("name", "description", "developer_instructions"):
                if not data.get(key):
                    errors.append(f"{path.name} no define {key}")
            name = data.get("name", "")
            if name in names:
                errors.append(f"Nombre de agente duplicado: {name}")
            names.add(name)
            if name != "broker" and data.get("sandbox_mode") != "read-only":
                errors.append(f"{path.name} debe ser read-only")

    gitignore = (root / ".gitignore").read_text(encoding="utf-8") if (root / ".gitignore").exists() else ""
    for pattern in ("inbox/*", "private/*", "workspace/agencies/*"):
        if pattern not in gitignore:
            errors.append(f".gitignore no protege {pattern}")

    durable_root = root / "knowledge" / "agencies"
    pii_patterns = {
        "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
        "iban": re.compile(r"\bES\d{22}\b", re.IGNORECASE),
        "dni_nie": re.compile(r"\b(?:\d{8}[A-Z]|[XYZ]\d{7}[A-Z])\b", re.IGNORECASE),
        "secret": re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*\S+"),
    }
    if durable_root.is_dir():
        for path in durable_root.rglob("*"):
            if not path.is_file() or "_template" in path.parts:
                continue
            if path.suffix.lower() != ".md":
                errors.append(f"Archivo no Markdown en memoria durable: {path.relative_to(root)}")
                continue
            content = path.read_text(encoding="utf-8")
            if re.search(r"(?m)^classification:\s*(confidential|restricted)\s*$", content):
                errors.append(f"Conocimiento no versionable por clasificacion: {path.relative_to(root)}")
            if re.search(r"(?m)^contains_personal_data:\s*(?!false\s*$)\S+", content):
                errors.append(f"Datos personales no depurados en {path.relative_to(root)}")
            for label, pattern in pii_patterns.items():
                if pattern.search(content):
                    errors.append(f"Posible {label} en conocimiento versionable: {path.relative_to(root)}")

    if (root / ".git").is_dir():
        try:
            tracked = subprocess.run(
                ["git", "ls-files"], cwd=root, check=True, capture_output=True, text=True
            ).stdout.splitlines()
            for item in tracked:
                normalized = item.replace("\\", "/")
                if normalized.startswith(("inbox/", "private/")) and not normalized.endswith(".gitkeep"):
                    errors.append(f"Archivo privado rastreado por Git: {normalized}")
                if normalized.startswith("workspace/agencies/") and not normalized.startswith("workspace/agencies/_template/"):
                    errors.append(f"Expediente operativo rastreado por Git: {normalized}")
        except (OSError, subprocess.CalledProcessError) as exc:
            errors.append(f"No se pudo comprobar git ls-files: {exc}")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    agency = subparsers.add_parser("new-agency")
    agency.add_argument("display_name")
    agency.add_argument("--slug")

    case = subparsers.add_parser("new-case")
    case.add_argument("agency_slug")
    case.add_argument("objective")
    case.add_argument("--operation-type", default="unknown")
    case.add_argument("--jurisdiction", default="unknown")
    case.add_argument("--case-id")

    source = subparsers.add_parser("register-source")
    source.add_argument("agency_slug")
    source.add_argument("case_id")
    source.add_argument("objective")
    group = source.add_mutually_exclusive_group(required=True)
    group.add_argument("--file")
    group.add_argument("--url")
    source.add_argument(
        "--classification",
        choices=("public", "internal", "confidential", "restricted"),
        default="confidential",
    )

    close = subparsers.add_parser("close-case")
    close.add_argument("agency_slug")
    close.add_argument("case_id")

    subparsers.add_parser("validate")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = REPO_ROOT
    try:
        if args.command == "new-agency":
            result = create_agency(root, args.display_name, args.slug)
            print(result)
        elif args.command == "new-case":
            result = create_case(
                root,
                args.agency_slug,
                args.objective,
                args.operation_type,
                args.jurisdiction,
                args.case_id,
            )
            print(result)
        elif args.command == "register-source":
            result = register_source(
                root,
                args.agency_slug,
                args.case_id,
                args.objective,
                args.file,
                args.url,
                args.classification,
            )
            print(result)
        elif args.command == "close-case":
            print(close_case(root, args.agency_slug, args.case_id))
        else:
            errors = validate(root)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print("BROKER workspace valido")
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI returns a concise failure
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
