# Reanudación por ejecución

El único emisor del experimento integrado es ExecStopPost del runner independiente,
una vez concluida su limpieza. El coordinador de consola no envía una segunda
notificación. Su cierre y restauración de VT tienen evidencia separada; un evento
del runner no acredita esa restauración ni ejecución posterior del modelo.

El cliente genera UUID y directorio antes de arrancar el runner. El manifiesto
inmutable vincula nombre, unidad propietaria, checkpoint y destino explícito
ARCHTV_CODEX_REMOTE/ARCHTV_CODEX_THREAD. El runner recibe ARCHTV_RUN_CHECKPOINT.
El puntero apex-current-checkpoint queda sólo para navegación humana.

Un flock exclusivo protege un registro reemplazado atómicamente con fsync.
Se registra sending antes de contactar Codex: queued sólo acredita aceptación
de cola; no acredita que la continuación se ejecutó. Un fallo/timeout o sending
abandonado es indeterminado y nunca se reenvía automáticamente. Contrastar UUID
con la cola/hilo y registrar recepción/ejecución efectiva antes de decidir una
reentrega manual. No existe garantía distribuida de exactamente una entrega;
se garantiza como máximo un intento automático por ejecución. El socket fijado
puede caducar al reiniciar Codex: se conserva el error, sin descubrir otro destino.

Si el coordinador falla antes de crear el runner, no hay evento automático:
consultar su checkpoint y journal. No se fabrica un resultado terminal.
Cada aviso es breve y nombra el experimento real. No hay timers ni sondeos del
modelo. Tests con sender simulado: `python tests/automation/test_run_completion.py`;
no envían mensajes al hilo. Cubren éxito, fallo, ocho callbacks concurrentes,
repetición, silencio no terminal y entrega indeterminada.

## Auditoría de migración 2026-11-02

Checkpoint: /home/tv/recuperacion-archtv/20261102T005219Z-resume-repair.
HEAD inicial 9e18bdd, sincronizado. Pendientes runtime y doce históricos conservados.
Causa: plantilla apexd usada también para Markor, puntero global mutable,
comprobación de existencia sin lock y fallback de segundo emisor.
El callback cacheado apex-completion.py se archivó y quedó inerte, para que
un reinicio manual de unidades históricas no vuelva a llenar la cola cancelada.
Los avisos históricos tienen ejecuciones distintas: no se eliminan como duplicados.

Productores encontrados: callback cacheado APEX; ExecStopPost del cliente integrado;
fallback del coordinador; wake-on-package.py (pidfd de empaquetado ya concluido);
resume-after-boot.py (servicio archtv-kernel-boot-resume deshabilitado, no activo).
Unidades APEX históricas fallidas son transitorias, no activas, sin Restart.
No timers archtv activos. El watcher nativo de Input captura evidencia, no envía
mensajes. No hay herramienta general automation_update disponible en esta sesión;
no se afirma haber inspeccionado automatizaciones externas no accesibles.
