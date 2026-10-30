# La APK usa el Looper principal original de AOSP

El runtime combinado ejecuta el DEX original del contador sobre ART y usa
Looper/Handler/MessageQueue portados desde AOSP para su hilo UI. Las 19 fuentes
seleccionadas siguen sin cambios. Activity, View, Bundle, recursos y preferencias
siguen siendo el subconjunto propio: el framework completo aún no está portado.

## Ensamblado y ejecución

build_aosp_queue.py genera framework.jar antes de compilar los comprobadores.
build_apk_runtime.py verifica su hash, rechaza clases de comprobación/java.* y
lo combina con el anfitrión mediante D8. No incorpora la referencia completa,
declaraciones auxiliares ni fuentes de la APK. Registra la procedencia original.

El proceso requiere -Darchtv.linux.library. archtv-apk-host obtiene la ruta de
ARCHTV_APK_LINUX_LIBRARY y la pasa como argumento, sin shell. El comprobador sin
ventana usa --linux-library. Si falta, falla: no vuelve al antiguo bucle propio.

## Hilo y cierre

prepareMainLooper original configura el principal. getMainLooper y myLooper deben
coincidir en cada callback. Un mensaje Handler construye la Activity y ejecuta
hostCreate. Un lector separado publica comandos en ese Handler con un semáforo de
16 pendientes; no descarta entradas ni modifica vistas desde el lector.

El principal original no admite quit de la aplicación. El cierre del anfitrión
ejecuta hostDestroy en un mensaje UI y desenrolla loop con una señal privada.
Después reutiliza dispose original por reflexión y cierra el bloqueo de datos.
No modifica MessageQueue ni permite quit del principal. Los fallos de callback
intentan destruir la Activity en UI y se propagan sin emitir closed como éxito.
El lector es daemon para no retener un proceso fallido. Este cierre es una
adaptación privada ligada a la revisión fijada, no una API Android pública.

## Evidencia

reports/aosp-ui-headless verifica la APK original, 0→1→2, nuevo proceso 2→3,
bloqueo exclusivo, permisos y recursos. Una ráfaga de 64 activaciones sobre la
entrada limitada a 16 incrementa exactamente una vez por entrada. Las trazas
sitúan creación, activaciones y cierre en main. EOF cierra ordenadamente; un
comando inválido muestra la pila Handler/Looper original, limpia y permite reabrir.
También pasan las regresiones de recursos truncados y preferencias corruptas.

reports/aosp-main-ui-wayland registra dos sesiones DRM/Pixman 1280×720:
uinput→libinput→Wayland→Rust→Handler original→listener de la APK. Enter/Espacio
incrementan hasta 2; la reapertura conserva 2 y avanza a 3. Los buffers DRM y los
últimos frames del cliente coinciden exactamente en RGB. Se incluyen trazas del
principal y hashes del enlace nativo. Waydroid permaneció inactivo; al terminar
no quedaron procesos de compositor/cliente/ART ni sesión local, y volvió tty1.

La invalidación visual sigue ligada a las instantáneas del protocolo de entrada:
todavía no se redibujan automáticamente los cambios asíncronos de View. Faltan
Activity/View/recursos originales, Bundle/Parcel/Binder IPC, servicios, aislamiento,
ampliación de APK y pruebas de rendimiento/estabilidad. H7 y la distribución siguen
abiertos; esta regresión no acredita compatibilidad general.
