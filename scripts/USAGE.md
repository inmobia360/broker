# Utilidades de BROKER

Validar la estructura:

```powershell
python scripts/broker_workspace.py validate
```

Crear una agencia:

```powershell
python scripts/broker_workspace.py new-agency "Inmobiliaria Milenio"
```

Abrir un expediente:

```powershell
python scripts/broker_workspace.py new-case inmobiliaria-milenio "Revisar el encargo de intermediacion" --operation-type sale --jurisdiction es-ga
```

Registrar un adjunto sin incorporarlo a Git:

```powershell
python scripts/broker_workspace.py register-source inmobiliaria-milenio CASE-20260907-0001 "Revisar clausulas y faltantes" --file "C:\ruta\encargo.pdf" --classification confidential
```

Registrar una URL con un objetivo acotado:

```powershell
python scripts/broker_workspace.py register-source inmobiliaria-milenio CASE-20260907-0001 "Comprobar requisitos de publicacion" --url "https://sitio.example/recurso" --classification public
```

Registrar una fuente no descarga ni recorre la URL. BROKER debe consultar despues el recurso concreto con las herramientas y permisos disponibles y completar la ficha de evidencia.

Cerrar un expediente despues de que `quality.md` tenga `decision: approved`:

```powershell
python scripts/broker_workspace.py close-case inmobiliaria-milenio CASE-20260907-0001
```

El comando rechaza el cierre mientras CONTROL DE CALIDAD no lo haya aprobado.
