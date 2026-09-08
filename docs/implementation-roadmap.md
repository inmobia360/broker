# Hoja de ruta de implementación

## MVP de validación del staff

1. Identificación inequívoca de agencia y expediente.
2. Contrato común con `tenant_id`, estados y escalado.
3. Coordinación controlada entre especialistas.
4. Revisión independiente de CALIDAD.
5. Pruebas de aislamiento y cierre.

## Piloto

Validar un flujo completo con una única agencia autorizada, midiendo preguntas evitables, bloqueos, contradicciones detectadas, tiempos por tarea, rechazos de calidad y trazabilidad.

## Escalado CRM

Añadir un directorio de tenants, interfaces de adaptadores CRM, permisos por rol, auditoría protegida y pruebas de aislamiento a nivel de servicio. No se deben introducir integraciones externas hasta que el flujo del staff pase el piloto.
