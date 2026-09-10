# Flujo SDD de AI BROKER

Cada funcionalidad se trabaja en una carpeta `specs/<id>-<slug>/` con estos artefactos:

1. `spec.md`: contexto, usuarios, historias, requisitos EARS, casos límite, fuera de alcance y dudas.
2. Clarificación: revisión crítica de ambigüedades, riesgos y dependencias antes de planificar.
3. `plan.md`: arquitectura, datos, seguridad, interfaces y decisiones técnicas.
4. `tasks.md`: tareas pequeñas, ordenadas y con condición explícita de «hecho cuando».
5. Implementación: una tarea cada vez, con tests y sin mezclar cambios no especificados.
6. `validation.md`: recorrido requisito por requisito con evidencia de tests, seguridad y revisión humana.

Los cambios de alcance actualizan primero `spec.md`, después el plan y las tareas. No se marca completada una funcionalidad por compilar: debe cumplir sus criterios de aceptación y pasar control de calidad.
