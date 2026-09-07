# Puertas de calidad

CALIDAD aprueba solo cuando se cumple todo lo aplicable:

- agencia y expediente correctos;
- objetivo y alcance satisfechos;
- fuentes identificadas y vigentes;
- hechos separados de estimaciones y recomendaciones;
- territorio y fecha normativa determinados;
- contradicciones y faltantes visibles;
- datos personales minimizados y rutas privadas respetadas;
- no se afirma haber ejecutado una accion sin evidencia;
- actuaciones externas autorizadas de forma explicita;
- decisiones sensibles sujetas a control humano;
- entregable util, consistente y accionable;
- propuestas de memoria aceptadas, rechazadas o pendientes.

La salida contiene `decision: approved|rejected`, `reviewed_at`, `reviewed_by: control_calidad`, `approval_id` con formato `QA-*`, los cuatro indicadores booleanos (`evidence_complete`, `privacy_checked`, `authorizations_checked`) y hallazgos, evidencias revisadas y correcciones exigidas. Sin todos esos valores y `approved`, BROKER no marca `closed`.
