from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.broker_workspace import (
    close_case,
    create_agency,
    create_case,
    register_source,
    slugify,
    validate,
)


ROOT = Path(__file__).resolve().parents[1]


class BrokerWorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        test_tmp = ROOT / "tmp" / "tests"
        test_tmp.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=test_tmp)
        self.root = Path(self.temp.name)
        for relative in ("knowledge", "workspace", ".codex", "skills"):
            shutil.copytree(ROOT / relative, self.root / relative)
        shutil.copy2(ROOT / "AGENTS.md", self.root / "AGENTS.md")
        shutil.copy2(ROOT / ".gitignore", self.root / ".gitignore")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_slugify_spanish_name(self) -> None:
        self.assertEqual(slugify("Inmobiliaria Milenio S.L."), "inmobiliaria-milenio-s-l")

    def test_agencies_and_cases_are_isolated(self) -> None:
        create_agency(self.root, "Inmobiliaria Milenio")
        create_agency(self.root, "Costa Norte")
        first = create_case(
            self.root,
            "inmobiliaria-milenio",
            "Revisar un encargo",
            "sale",
            "es-ga",
            "CASE-TEST-0001",
        )
        second = create_case(
            self.root,
            "costa-norte",
            "Preparar un anuncio",
            "rental",
            "es-as",
            "CASE-TEST-0001",
        )
        self.assertNotEqual(first.parent.parent, second.parent.parent)
        self.assertIn("inmobiliaria-milenio", (first / "request.md").read_text(encoding="utf-8"))
        self.assertIn("costa-norte", (second / "request.md").read_text(encoding="utf-8"))

    def test_register_url_records_objective_without_fetching(self) -> None:
        create_agency(self.root, "Inmobiliaria Milenio")
        create_case(
            self.root,
            "inmobiliaria-milenio",
            "Consultar requisitos oficiales",
            case_id="CASE-TEST-0002",
        )
        record = register_source(
            self.root,
            "inmobiliaria-milenio",
            "CASE-TEST-0002",
            "Localizar campos obligatorios",
            None,
            "https://example.com/resource",
            "public",
        )
        content = record.read_text(encoding="utf-8")
        self.assertIn("source_type: url", content)
        self.assertIn("Localizar campos obligatorios", content)
        self.assertIn("status: draft", content)

    def test_register_attachment_is_copied_to_private_inbox_and_hashed(self) -> None:
        create_agency(self.root, "Inmobiliaria Milenio")
        create_case(
            self.root,
            "inmobiliaria-milenio",
            "Revisar documentacion",
            case_id="CASE-TEST-0003",
        )
        attachment = self.root / "sample-contract.txt"
        attachment.write_text("contenido de prueba", encoding="utf-8")
        record = register_source(
            self.root,
            "inmobiliaria-milenio",
            "CASE-TEST-0003",
            "Identificar clausulas pendientes",
            str(attachment),
            None,
            "confidential",
        )
        content = record.read_text(encoding="utf-8")
        self.assertIn("source_type: attachment", content)
        self.assertIn("inbox/inmobiliaria-milenio/CASE-TEST-0003/", content)
        self.assertNotIn("sha256: unknown", content)
        stored_files = list(
            (self.root / "inbox" / "inmobiliaria-milenio" / "CASE-TEST-0003").iterdir()
        )
        self.assertEqual(len(stored_files), 1)

    def test_existing_slug_with_different_agency_requires_confirmation(self) -> None:
        create_agency(self.root, "Inmobiliaria Milenio")
        with self.assertRaises(FileExistsError):
            create_agency(self.root, "Milenio Inversiones", "inmobiliaria-milenio")

    def test_path_traversal_slug_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            create_case(self.root, "../../otra-agencia", "Objetivo")

    def test_path_traversal_case_id_is_rejected(self) -> None:
        create_agency(self.root, "Inmobiliaria Milenio")
        with self.assertRaises(ValueError):
            register_source(
                self.root, "inmobiliaria-milenio", "../../CASE-ESCAPE", "Objetivo",
                None, "https://example.com/resource", "public"
            )

    def test_url_credentials_and_private_ip_are_rejected(self) -> None:
        create_agency(self.root, "Inmobiliaria Milenio")
        create_case(self.root, "inmobiliaria-milenio", "Revisar fuente", case_id="CASE-TEST-0005")
        for unsafe in ("https://user:pass@example.com/file", "http://127.0.0.1/private"):
            with self.assertRaises(ValueError):
                register_source(
                    self.root, "inmobiliaria-milenio", "CASE-TEST-0005", "Objetivo",
                    None, unsafe, "public"
                )

    def test_url_query_is_redacted_from_record(self) -> None:
        create_agency(self.root, "Inmobiliaria Milenio")
        create_case(self.root, "inmobiliaria-milenio", "Revisar fuente", case_id="CASE-TEST-0006")
        record = register_source(
            self.root, "inmobiliaria-milenio", "CASE-TEST-0006", "Objetivo",
            None, "https://example.com/file?token=secret#section", "public"
        )
        self.assertNotIn("token=secret", record.read_text(encoding="utf-8"))
        private_urls = list((self.root / "private" / "inmobiliaria-milenio" / "CASE-TEST-0006").glob("*.url"))
        self.assertEqual(len(private_urls), 1)

    def test_case_cannot_close_without_quality_approval(self) -> None:
        create_agency(self.root, "Inmobiliaria Milenio")
        case = create_case(
            self.root,
            "inmobiliaria-milenio",
            "Revisar contrato",
            case_id="CASE-TEST-0004",
        )
        with self.assertRaises(PermissionError):
            close_case(self.root, "inmobiliaria-milenio", "CASE-TEST-0004")
        quality = case / "quality.md"
        quality.write_text(
            quality.read_text(encoding="utf-8")
            .replace("decision: pending", "decision: approved")
            .replace("reviewed_at: null", "reviewed_at: 2026-09-07T12:00:00Z")
            .replace("approval_id: null", "approval_id: QA-TEST-0001")
            .replace("evidence_complete: false", "evidence_complete: true")
            .replace("privacy_checked: false", "privacy_checked: true")
            .replace("authorizations_checked: false", "authorizations_checked: true"),
            encoding="utf-8",
        )
        close_case(self.root, "inmobiliaria-milenio", "CASE-TEST-0004")
        self.assertIn("status: closed", (case / "closure.md").read_text(encoding="utf-8"))

    def test_repository_structure_is_valid(self) -> None:
        self.assertEqual(validate(self.root), [])


if __name__ == "__main__":
    unittest.main()
