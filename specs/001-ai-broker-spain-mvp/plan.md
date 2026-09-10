# Plan técnico: AI Broker Spain MVP

## Capas

1. Web SaaS y autenticación por invitación.
2. API multi-tenant con autorización por `tenant_id`.
3. Persistencia de agencias, usuarios, expedientes, fuentes, tareas y auditoría.
4. Almacenamiento privado de documentos.
5. Orquestador BROKER y contratos de salida de subagentes.
6. Servidor MCP con tokens revocables.
7. Adaptador de país `spain` para reglas y fuentes.
8. Límites freemium preparados, Stripe inactivo.

## Decisiones de seguridad

- Secretos solo en variables de entorno o almacén cifrado.
- PII separada de conocimiento versionable.
- Logs sin contenido de documentos ni tokens.
- Acciones externas bloqueadas hasta autorización.
- Validación de tamaño, tipo y contenido de adjuntos.

## Orden de entrega

Autenticación/invitaciones -> aislamiento multi-tenant -> expedientes -> BROKER/subagentes -> documentos -> conocimiento -> MCP -> panel y límites -> validación.
