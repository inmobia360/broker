# Arquitectura multiagencia

El núcleo es global y reutilizable. La configuración y el conocimiento durable se separan por agencia; los datos de clientes, documentos y conversaciones permanecen fuera del conocimiento global y fuera de Git.

## Identidad de agencia

```yaml
tenant_id: tenant-af-inmobiliaria
agency_slug: af-inmobiliaria
```

`tenant_id` es la clave estable que deberá utilizar en el futuro un CRM, API, base de datos o sistema de permisos. `agency_slug` se conserva para rutas humanas y compatibilidad con la estructura actual. No se permite procesar una solicitud sin ambos valores resueltos.

La resolución futura podrá sustituirse por un directorio o servicio de identidad sin cambiar los agentes:

```text
nombre de agencia -> directorio de agencias -> tenant_id + agency_slug -> expediente autorizado
```

La primera etapa valida el flujo de staff y sus controles dentro del repositorio. Los conectores CRM se diseñarán después como adaptadores que reciban siempre `tenant_id`.
