# Protocolo de sincronización de BROKER

En el primer chat del día, BROKER realiza una comprobación de solo lectura del repositorio local frente a `origin/main` antes de abrir memoria o expedientes de una agencia.

- **Sincronizado:** continúa sin mostrar un aviso innecesario.
- **Remoto por delante:** informa de que el repositorio local necesita actualizarse desde GitHub y solicita autorización para hacer `pull`.
- **Cambios locales o commits no publicados:** los comunica y no los sobrescribe ni hace `push` automáticamente.
- **Ramas divergentes o conflicto:** deja el expediente en espera y pide una decisión concreta.

La actualización nunca se ejecuta de forma silenciosa. El protocolo mantiene alineado el repositorio local con GitHub cuando el usuario lo autoriza; no concede a un entorno cloud acceso automático a carpetas exclusivas del ordenador.
