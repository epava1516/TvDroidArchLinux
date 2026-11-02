# Reanudación y consumo por ejecución

## Contrato vigente

Cada ejecución tiene un manifiesto de sólo lectura con UUID, nombre real, unidad
propietaria, checkpoint, destino y `active_owner` inmutables. El runner recibe
ARCHTV_RUN_CHECKPOINT. `apex-current-checkpoint` es sólo navegación humana.
Un único ExecStopPost recoge el resultado después de la limpieza del runner;
el coordinador de consola conserva aparte su restauración de VT, sin notificar.

**El consumidor predeterminado es la ejecución activa, no la cola.** Un único
flock de ejecución serializa callback, consumo, cesión y reclamación. El callback
conserva siempre completion-result.json, incluso sin mensaje. El consumidor queda
en completion-consumer.json. completion-delivery.json registra el envío o su
supresión. Los reemplazos son atómicos, con fsync de archivo y directorio.

Procedimiento del agente para cada manifiesto explícito (no usar el puntero global):

1. Al retomar, contrastar manifiesto, Git, procesos y resultado; leer consumer y
   delivery antes de procesarlo. Si está consumed, no repetir trabajo ni reencolar.
2. Con propiedad active, procesar el resultado y registrar:
   `python scripts/run_completion.py MANIFEST consume active:UUID`.
   Puede hacerse antes del callback si result.json ya contiene outer_exit terminal.
   Los callbacks posteriores conservarán la evidencia y guardarán consumed sin envío.
3. Sólo si el agente deja de observar esa ejecución y necesita una continuación,
   ceder explícitamente: `... MANIFEST handoff active:UUID`.
   Un resultado consumido no admite cesión. `claim-active` recupera una cesión
   todavía no enviada antes de que un nuevo turno empiece a procesarla.
4. Si el estado es sending/queued/indeterminate, no reclamar ni reenviar: contrastar
   la entrega real con la cola. queued sólo acredita aceptación, no recepción ni
   ejecución. Una notificación histórica ya procesada debe descartarse como trabajo
   redundante al entrar, conservando su evidencia; no ejecutar de nuevo el experimento.

Además existe un interruptor de envío: por defecto NO está presente
`/home/tv/.cache/archtv/completion-notifications.enabled`.
Incluso tras handoff, su ausencia conserva resultado y notifications_disabled sin
contactar Codex. **Permanece desactivado tras la revisión del 2 de noviembre.**
Activarlo no cede el consumo de ningún run: ambas condiciones son necesarias.
Un callback repetido puede entregar un resultado cedido antes silenciado, pero
nunca uno active/consumed. No hay reintentos de intentos ambiguos. Un crash tras
sending impide otro intento automático. No existe garantía distribuida de entrega
exactamente una vez; hay un consumidor local y como máximo un intento automático.
El socket fijado puede caducar: no se descubre otro destino ni se reenvía.

Si falla el coordinador antes de crear el runner no hay evento automático;
consultar su checkpoint/journal. No se fabrica resultado terminal. No hay timers,
sondeos del modelo ni mensajes de prueba al hilo.

## Evidencias y límites

`python tests/automation/test_run_completion.py`: éxito, fallo, ocho callbacks
concurrentes, repetición, no terminal, entrega indeterminada, activo con resultado
sin mensaje, consumo antes del callback, envíos desactivados, recuperación de
cesión sin envío y carrera callbacks/consumo activo. Sender simulado exclusivamente.

Checkpoint de corrección inicial: /home/tv/recuperacion-archtv/20261102T005219Z-resume-repair.
Checkpoint de coordinación: /home/tv/recuperacion-archtv/20261102T011336Z-result-consumer.
La corrección inicial sólo impedía duplicar *entregas*, pero cada runner seguía
encolando aunque el turno activo ya lo observase. Ésta era la acumulación restante:
los UUID distintos eran resultados reales, no callbacks necesariamente duplicados.

Se contrastaron los tres runs fc258592, 263a1327 y 71fdde53 con sus manifiestos,
resultados y recibos queued. Los tres resultados quedaron marcados consumed en sus propios checkpoints, con evidencia de migración; sus recibos queued se conservan. Esos recibos no prueban su presencia actual en cola.
El CLI instalado publica thread/queue/list y thread/queue/delete en su esquema
experimental. El intento de consulta mediante app-server proxy agotó initialize;
no envió ningún delete. Estado actual de esa cola: desconocido. No se tocaron bases
de datos internas ni se afirma haber cancelado los mensajes previos.

Productores auditados: callback APEX cacheado (archivado e inerte), ExecStopPost
integrado (único emisor actual), antiguo fallback del coordinador (retirado),
wake-on-package.py (empaquetado concluido), resume-after-boot.py (servicio deshabilitado).
Unidades históricas APEX fallidas son transitorias, sin Restart. No hay timers ni
unidades archtv ejecutándose al iniciar esta revisión. El watcher de Input sólo
captura evidencia. No hay herramienta general automation_update en esta sesión;
no se atribuye inspección de automatizaciones externas inaccesibles.
