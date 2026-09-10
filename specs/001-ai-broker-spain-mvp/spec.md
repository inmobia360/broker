# Especificación: AI Broker Spain MVP

## Contexto

Plataforma SaaS marca blanca para profesionales inmobiliarios freelance y agencias independientes en España. El MVP combina gestión general, captación de propiedades y documentos/contratos, con BROKER y subagentes, memoria aislada y conexión MCP.

## Usuarios

- Administrador de agencia invitado.
- Agente inmobiliario miembro de una agencia.
- Revisor de calidad.

## Requisitos funcionales (EARS)

- **RF-001** Cuando una persona acepta una invitación válida, el sistema debe crear su cuenta y asociarla únicamente a la agencia de la invitación.
- **RF-002** Cuando un usuario inicia su primera sesión, el sistema debe pedir o confirmar la agencia activa antes de leer memoria de cliente.
- **RF-003** Cuando el usuario crea un expediente, el sistema debe asignar un identificador único y aislar sus datos por `tenant_id`.
- **RF-004** Cuando el usuario envía una necesidad, BROKER debe clasificarla y enrutarla al conjunto mínimo de subagentes.
- **RF-005** Cuando se carga un documento o URL, el sistema debe registrar origen, objetivo, clasificación, autorización y estado de revisión.
- **RF-006** Cuando se propone conocimiento reutilizable, debe permanecer privado y pendiente hasta superar anonimización, calidad y autorización.
- **RF-007** Cuando una tarea requiere una acción externa, el sistema debe solicitar autorización inmediata y registrar la decisión.
- **RF-008** Cuando un expediente se cierra, CONTROL DE CALIDAD debe haber aprobado evidencia, privacidad, consistencia, vigencia y autorizaciones.
- **RF-009** Cuando el usuario configura MCP, el sistema debe emitir un token privado revocable y nunca mostrarlo completo después de su creación.

## Casos límite

- Invitación caducada, revocada o reutilizada.
- Agencia con slug parecido.
- Usuario sin agencia activa.
- Expedientes o archivos de otra agencia solicitados por error.
- Documento con datos personales o instrucciones maliciosas.
- Token revocado o perdido.
- Expediente con calidad rechazada.
- Falta de fuente oficial vigente para una respuesta legal.

## Fuera de alcance del MVP

- Cobros Stripe activos.
- Publicación automática en portales.
- WhatsApp y correo automatizados.
- Módulos legales de otros países.
- Conocimiento global compartido automáticamente.

## Criterios de finalización

- Cada RF tiene al menos un test o evidencia verificable.
- Existe prueba de aislamiento entre dos agencias.
- No se registran secretos ni PII en Git.
- Se prueban invitaciones, tokens, adjuntos y cierre de calidad.
- Se documenta configuración de Hostinger y MCP.
- CONTROL DE CALIDAD aprueba la validación.

## Dudas abiertas

- Motor de base de datos definitivo.
- Servicio de almacenamiento de documentos.
- Proveedor de correo transaccional.
- Plan exacto de Hostinger y capacidad de procesos MCP persistentes.
