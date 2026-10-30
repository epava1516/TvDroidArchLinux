# Handler y Looper originales ejecutan mensajes en Linux

El primer Runnable ya se ejecuta mediante Handler.post y Looper.loop originales
en ART. Se conservan sin cambios 19 fuentes Java de frameworks/base. El manifiesto
de estudio contiene ahora 32 archivos y 3 447 820 bytes; el JAR completo de referencia
sigue fuera del runtime y se usa sólo al compilar.

## Implementación y fronteras

Se añadieron Parcelable, SystemClock, ThreadLocalWorkSource, Binder, IBinder,
IntArray, BinderInternal, Process, ZygoteProcess, SystemProperties y
LocalSocketAddress originales a las ocho fuentes del ensayo JNI anterior.
Process inicializa un objeto ZygoteProcess que almacena direcciones de sockets;
no se ha iniciado ni conectado un servicio Zygote ni arrancado Android.
Process.myUid/myPid usan las llamadas Os de libcore/ART ya disponibles sobre Linux.

Las adaptaciones Rust son deliberadamente explícitas:

| Frontera | Implementación verificada | Alcance pendiente |
| --- | --- | --- |
| MessageQueue JNI | epoll/eventfd, despertar, listeners FD y destrucción | Resto de APIs y validaciones de concurrencia/estabilidad más amplias |
| SystemClock | CLOCK_MONOTONIC para uptime, CLOCK_BOOTTIME para tiempo con suspensión, reloj CPU de hilo y CLOCK_REALTIME | Servicios de hora de red/GNSS, ajustes de reloj y pruebas de suspensión real |
| Identidad Binder local | UID/PID Linux y token de identidad por hilo; no hay transacción entrante; vaciado de comandos vacío porque no existe transporte | Binder IPC, objetos remotos, Parcel, llamadas de servicios y políticas Android |
| SystemProperties.getInt(String,int) | Configuración local de sólo lectura desde ARCHTV_ANDROID_PROPERTY_ seguido de la clave, valor decimal o defecto | Servicio global Android, mutación, callbacks y acceso por handle; esas rutas siguen sin implementar |

SystemClock conserva su código Java y siete métodos CriticalNative, cuyo ABI no
recibe JNIEnv. Los relojes Linux seleccionados deben estar disponibles; el adaptador
aborta si clock_gettime falla, pues no puede devolver un tiempo falso ni lanzar una
excepción JNI desde ese ABI. No se ha probado funcionamiento con esas llamadas
bloqueadas. Los setters de propiedades y los métodos Binder sin implementar no
devuelven éxito ficticio: siguen fallando al intentar enlazarlos.

La compilación requiere además declaraciones auxiliares de setInt$ y
LambdaMetafactory. Las lambdas originales se desazucaran con D8; ninguna de esas
clases auxiliares se incorpora al DEX. La anotación UnsupportedAppUsage es sólo
metadato de compilación. No se ha sustituido el algoritmo de planificación Java.

## Pruebas y evidencia

reports/aosp-handler-foundations contiene procedencia y salidas de estos ensayos:

- Relojes: unidades de los siete enlaces, sleep original y conservación de interrupción.
- Identidad: UID/PID contra Os real, clear/restore y rechazo de getCallingUidOrThrow
  fuera de una transacción. Propiedades presentes, ausentes, malformadas y setter
  explícitamente no implementado.
- Un Runnable con Handler.post y salida normal de Looper.loop.
- FIFO, mensaje diferido sin entrega anticipada, cancelación, idle handler,
  propagación/restauración de WorkSource, entrega entre hilos, barrera síncrona con
  mensaje asíncrono, quit y quitSafely.
- Regresión JNI: listener público sobre tubería, despertar entre hilos y dispose.

La semántica de la cola pasó diez ejecuciones en procesos ART nuevos. No son una
prueba prolongada ni validan todos los métodos del framework. Una primera versión
de la prueba alcanzó 45 segundos sin guardar sus diagnósticos. Se añadieron trazas,
retención de salidas al vencer el plazo y trabajadores de prueba daemon para que
una aserción fallida no mantenga el proceso vivo; las rutas exitosas siguen haciendo
join de cada trabajador. No se ha determinado la causa de aquel primer bloqueo,
y no se atribuye a una corrección de la cola. El incidente se conserva en
initial-timeout.json; las pruebas posteriores no cierran la estabilidad de H7.

```bash
python tools/apk/build_aosp_queue.py --sources "$HOME/.cache/archtv/aosp-framework-study/pinned" --reference "$HOME/.cache/archtv/aosp-compile-tools/android-all-13.jar" --tools "$HOME/.cache/archtv/apk-build-tools" --output dist/apk/handler-nuevo
python tools/apk/verify_aosp_foundations.py --art "$HOME/.cache/archtv/art-host/host/art-13.0.0" --dex dist/apk/handler-nuevo/dex/classes.dex --library "$HOME/.cache/archtv/smithay/target/debug/libarchtv_aosp_linux.so" --output dist/apk/handler-prueba-nueva --queue-repeats 10
```

El ensayo FD requiere descriptores reales del host, como la prueba JNI previa.
La regresión final de los cinco comprobadores también pasa con el servicio
Waydroid detenido. Antes de detenerlo, el daemon estaba activo pero la sesión y
el contenedor LXC estaban STOPPED; esos estados se conservan por separado.

El ensayo descrito aquí precede a la integración en la APK. Esa integración ya
pasa la regresión sin ventana y Wayland: ver APK-LOOPER-AOSP.md. Activity, View, recursos originales, Parcel/Binder IPC y el resto del
framework continúan pendientes; no se acredita aún que la APK use este port.
