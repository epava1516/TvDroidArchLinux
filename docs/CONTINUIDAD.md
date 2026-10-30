# Checkpoint y recuperación

El contrato activo puede prohibir reinicios: un checkpoint no autoriza a reiniciar
VM o cliente si [CONTRATO-APK.md](CONTRATO-APK.md) lo impide.

El punto de entrada único es [ESTADO.md](ESTADO.md). Arquitectura explica decisiones;
ROADMAP y ROADMAP-A definen requisitos/aceptación; [EVIDENCIAS.md](EVIDENCIAS.md)
indexa resultados. Git conserva versiones. No hay RAG ni otro gestor de memoria.

## Al cerrar un hito o antes de interrumpir/reiniciar

1. Registrar objetivo/restricciones y siguiente acción concreta. Clasificar lo
   vigente, histórico, experimental y desconocido sin convertir planes en resultados.
2. Capturar `git status --short`, rama, `git rev-parse HEAD`, upstream y
   `git rev-list --left-right --count HEAD...origin/main`. Indicar si origin sólo
   es referencia local o si se contrastó con `git ls-remote origin refs/heads/main`.
3. Distinguir cambios propios y ajenos. Guardar parches y archivos nuevos fuera
   del árbol si habrá interrupción; no aplicar ni descartar automáticamente.
   La ubicación local es un snapshot de recuperación, no otra fuente de estado vigente.
4. Registrar PID y arranque/estado observado, unidad systemd, session_id/cell_id,
   operación y salida de evidencia de cada trabajo activo. Un fichero de lock o
   un PID antiguo no prueba actividad. Estados: activo observado, terminal,
   desconocido. No guardar argumentos, entorno ni tokens sensibles.
5. Enlazar resultados originales con alcance, limitaciones, commit fuente o hash
   de artefacto y fecha. Evitar pegar logs grandes; conservar hash si el artefacto
   sólo existe en caché y declarar esa dependencia local.
6. Actualizar estado/índice, comprobar enlaces y hashes y ejecutar Graphify según
   AGENTS.md. Commit y push sólo de los archivos del hito. No incorporar cambios
   ajenos ni credenciales. Antes de reiniciar, dejar instrucciones para retomar.

## Al retomar

- Comparar snapshot con HEAD, diff y upstream actuales. No restaurar parches sobre
  cambios ya presentes. Leer AGENTS.md y usar Graphify antes de buscar código.
- Revalidar handles reales (poll de sesión, `systemctl show`, `/proc/<pid>/stat` y
  tiempo de arranque). No relanzar por un timeout de observación: confirmar antes
  si el trabajo terminó. Si el handle falta, registrar ese hecho.
- Comprobar existencia y SHA-256 de evidencias. Un reporte verde no acredita más
  alcance que sus entradas, assertions y artefactos. Si falta evidencia: desconocido.
- Para MCP comprobar herramientas y una llamada real en el hilo; configuración,
  skill instalada y CLI sana no prueban conexión. Preservar límites estático/runtime.
- Seguir la siguiente acción vigente. Las autorizaciones persisten, pero no se
  infieren permisos de reinicio de VM o publicación de datos de un snapshot.

El [checkpoint fechado](../reports/continuidad-20261030/checkpoint.json) ilustra el
formato sin automatización adicional. El desvío organizativo termina con este
procedimiento y el índice; no abre una plataforma de documentación nueva.
