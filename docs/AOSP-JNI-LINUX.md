# MessageQueue original: enlace JNI Linux en Rust

archtv-aosp-linux es una biblioteca cdylib Rust que exporta los seis puntos JNI
de MessageQueue original. Utiliza epoll para eventos de FD y eventfd para despertar
la espera. No sustituye los algoritmos Java de ordenación y despacho por una cola
propia. Los identificadores nativos consultan un registro de Arc, evitando exponer
punteros Rust a Java; cada descriptor de escucha lleva una generación para no
aplicar el resultado de un callback a un registro sustituido durante ese callback.

## Fuentes originales y adaptación

El conjunto original compilado ahora contiene Looper, Handler, Message,
MessageQueue, SparseArray, ContainerHelpers, ArrayUtils y GrowingArrayUtils.
Las ocho fuentes de frameworks/base conservan sus hashes originales, sin parches.
SparseArray y sus utilidades se incorporaron después de observar su ausencia al
ejecutar dispatchEvents en ART. La referencia de API internas y las declaraciones
auxiliares siguen siendo exclusivamente de compilación.

El manifiesto de estudio pasa de 17 a 21 archivos (3 205 729 bytes). El informe
inicial de reports/aosp-framework-study conserva su instantánea de 17; el nuevo
inventario está en reports/aosp-queue-jni/source-dependencies/.

## Pruebas verificadas

Cuatro pruebas Rust verifican despertar retenido, despertar desde otro hilo,
callback de FD con retirada y sustitución del registro dentro de un callback.
Se ejecutan con sockets Unix reales del host. En el entorno aislado, dos pruebas
devuelven EPERM al registrar esos sockets en epoll; ejecutadas fuera de ese
aislamiento pasan. No se cambió el comportamiento del backend para ocultar ese error.

NativeQueueProbe carga la biblioteca Rust en ART y usa Looper/MessageQueue
originales. Verifica creación, estado de espera, despertar antes de esperar y
desde otro hilo, listener público sobre una tubería Linux, lectura del byte 42,
retirada del listener y dispose original. Termina con AOSP_QUEUE_JNI_OK y código 0.
El callback ejecuta dispatchEvents y SparseArray originales, no una función
simulada del anfitrión. Los errores Java pendientes se conservan en el paso JNI.

```bash
CARGO_TARGET_DIR="$HOME/.cache/archtv/smithay/target" cargo build --offline -j1 -p archtv-aosp-linux
python tools/apk/build_aosp_queue.py --sources "$HOME/.cache/archtv/aosp-framework-study/pinned" --reference "$HOME/.cache/archtv/aosp-compile-tools/android-all-13.jar" --tools "$HOME/.cache/archtv/apk-build-tools" --output dist/apk/cola-jni-nueva
python tools/apk/verify_aosp_jni.py --art "$HOME/.cache/archtv/art-host/host/art-13.0.0" --dex dist/apk/cola-jni-nueva/dex/classes.dex --library "$HOME/.cache/archtv/smithay/target/debug/libarchtv_aosp_linux.so" --output dist/apk/cola-jni-prueba-nueva
```

## Puerta que sigue abierta

HandlerDispatchProbe intenta postear un Runnable y ejecutar Looper.loop. Falla
con NoClassDefFoundError por android.os.Parcelable. Ese resultado está conservado
como siguiente dependencia observada, no como prueba del despacho. Todavía faltan
dependencias como Parcelable/Parcel, reloj, identidad, trazas y las que revele la
ejecución posterior; no se presupone que ese inventario sea completo.

native_queue_jni_pass=true acredita las pruebas indicadas, mientras
handler_dispatch_pass=false y apk_uses_original_framework=false permanecen
explícitos. El contador y su cliente Wayland siguen usando el prototipo propio.
No se cierra el port del framework, seguridad, compatibilidad general ni estabilidad.
