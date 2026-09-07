# Arquitectura del staff inmobiliario

## Principios

BROKER es el unico interlocutor y escritor canonico. Los especialistas trabajan con encargos acotados y devuelven resultados estructurados. COORDINADOR mantiene el plan y propone aprendizaje; CALIDAD acepta o rechaza el cierre. Los datos se aislan por agencia y expediente.

```text
Usuario
  -> BROKER
      -> COORDINADOR
      -> especialistas necesarios
      -> CONTROL DE CALIDAD
  <- respuesta consolidada de BROKER
```

## Estados del expediente

`intake -> triaged -> in_progress -> quality_review -> approved -> closed`

Estados alternativos: `waiting_user`, `blocked`, `cancelled` y `reopened`.

No se salta `quality_review`. Un resultado rechazado vuelve a `in_progress` con observaciones verificables.

## Dos almacenes, tres memorias

- `knowledge/global/`: fuentes, criterios y procedimientos comunes.
- `knowledge/agencies/<slug>/`: memoria durable, depurada y autorizada de una agencia.
- `workspace/agencies/<slug>/cases/<id>/`: memoria temporal y sensible del expediente, excluida de Git.

Los adjuntos originales se guardan en `inbox/` o `private/`, fuera de Git. El repositorio solo conserva conocimiento reutilizable que haya superado revisión.

El aislamiento dentro de un único checkout es operativo, no criptográfico: un proceso con permiso de lectura sobre el repositorio podría abrir otras carpetas. BROKER debe proporcionar a cada subagente solo los archivos y extractos necesarios. Si una agencia exige separación fuerte, se utilizarán un repositorio, almacenamiento y política de acceso independientes.

## Memoria permitida por rol

| Rol | Memoria necesaria |
|---|---|
| BROKER | `agency.md`, `decisions.md`, `memory/broker.md`, expediente activo |
| COORDINADOR | `memory/coordinador.md`, expediente activo y propuestas |
| CALIDAD | expediente activo, fuentes citadas y `memory/calidad.md` |
| Legal y cumplimiento | `memory/legal.md`, fuentes legales globales y expediente relevante |
| Captación, CRM y demanda | `memory/comercial.md`, `memory/operaciones.md` y expediente relevante |
| Documentación, publicación y marketing | `memory/operaciones.md`, `memory/comercial.md` y expediente relevante |
| Visitas, negociación y financiación | expediente relevante y solo la memoria necesaria para la tarea |
| Administración, fiscal y posventa | `memory/operaciones.md`, `memory/legal.md` y expediente relevante |
| Reporting y conocimiento | métricas agregadas, `decisions.md`, propuestas y fuentes; nunca datos personales sin depurar |

BROKER debe materializar este contexto mínimo en cada encargo. Que un agente pueda leer el checkout completo no significa que esté autorizado a hacerlo.

## Ingesta

1. Registrar agencia, expediente, fuente, objetivo, alcance y permiso.
2. Preservar el original y calcular su huella cuando sea posible.
3. Extraer solo la informacion necesaria.
4. Clasificar confidencialidad, datos personales, jurisdiccion y vigencia.
5. Producir una ficha Markdown con citas o localizadores.
6. Usar la ficha en el expediente.
7. Proponer conocimiento durable al cierre.
8. Aprobar, rechazar o marcar como sustituido; nunca sobrescribir silenciosamente.

## Regla de concurrencia

Se permite trabajo paralelo de lectura: investigacion, clasificacion, comprobacion y revision. Las escrituras en expedientes y conocimiento se serializan a traves de BROKER. Esto mantiene una sola fuente de verdad y evita conflictos entre subagentes.
