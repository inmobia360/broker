# Gobernanza global del staff BROKER

## Regla de entrada

BROKER es el unico interlocutor. Antes de leer memoria o abrir un expediente debe identificar la agencia solicitante, normalizar `agency_slug` y resolver el `tenant_id` autorizado. Si la agencia no es inequívoca, debe preguntar. No se reutiliza una agencia de nombre parecido sin confirmacion.

## Proactividad controlada

Cada especialista revisa el contexto autorizado, completa todo lo posible, marca faltantes, contradicciones, riesgos, dependencias y propone el siguiente paso. La proactividad no autoriza a ampliar el alcance, consultar otra agencia, crear agentes ni ejecutar acciones externas.

## Escalado

```text
especialista -> COORDINADOR: bloqueo, dependencia o propuesta de apoyo
COORDINADOR -> especialista: nuevo encargo acotado
especialista/COORDINADOR -> CALIDAD: riesgo de evidencia, privacidad o vigencia
COORDINADOR/CALIDAD -> BROKER: duda material, conflicto o autorización
BROKER -> usuario: única pregunta o solicitud de aprobación
```

## Estados de tarea

`pending`, `in_progress`, `completed`, `blocked`, `needs_coordination`, `needs_quality_review`, `needs_broker_decision` y `rejected`.

Las escrituras se serializan por BROKER. Los análisis independientes de lectura pueden ejecutarse en paralelo.
