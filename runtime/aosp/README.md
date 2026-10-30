# Port del framework original: primer cierre de compilación

framework-study.json fija las fuentes originales. El primer conjunto compilado
es Looper, Handler, Message y MessageQueue de frameworks/base Android 13,
sin cambios en sus fuentes. Los archivos se conservan en caché, fuera del repo;
el constructor verifica sus hashes antes de compilar.

## Referencia de compilación

El SDK público API 28 no contiene sus API internas: la compilación inicial produjo
170 errores. compile-reference.json fija org.robolectric:android-all:13-robolectric-9030017,
178 380 165 bytes. Se usa exclusivamente como referencia de clases al compilar.
Según la [arquitectura de Robolectric](https://robolectric.org/architecture/), los
JAR android-all contienen implementación del framework, a diferencia del SDK de
firmas públicas. Aquí no se usa el runner, instrumentación ni shadows de Robolectric.
Tampoco se añade ese JAR al classpath de ejecución.

Dos declaraciones auxiliares resuelven datos ausentes de esa referencia: la
anotación UnsupportedAppUsage y FileDescriptor.getInt$. Son sólo para compilar;
compile-stubs nunca se empaqueta en queue.jar ni en el DEX. ART/libcore proporciona
el FileDescriptor real; la prueba verifica su método getInt$ por reflexión.
La referencia no es una compilación propia del framework ni garantiza que todos
sus detalles internos coincidan con la revisión de fuentes fijada.

```bash
python tools/apk/fetch_compile_reference.py "$HOME/.cache/archtv/aosp-compile-tools"
python tools/apk/build_aosp_queue.py --sources "$HOME/.cache/archtv/aosp-framework-study/pinned" --reference "$HOME/.cache/archtv/aosp-compile-tools/android-all-13.jar" --tools "$HOME/.cache/archtv/apk-build-tools" --output dist/apk/cola-original-nueva
python tools/apk/probe_aosp_queue.py --art "$HOME/.cache/archtv/art-host/host/art-13.0.0" --dex dist/apk/cola-original-nueva/dex/classes.dex --output dist/apk/cola-enlace-nueva
```

## Resultado y siguiente frontera

La compilación original y D8 terminan correctamente. queue.jar incluye sólo las
clases originales y sus internas más QueueLinkProbe, separado de la app del
contador. La ejecución ART llega a Looper.prepare → constructor MessageQueue →
nativeInit y termina con UnsatisfiedLinkError. Ver reports/aosp-queue-compile/.
El código 0 del comprobador significa que observó esa frontera esperada, no que
funcione una cola. result.json mantiene queue_functional_pass=false.

En el primer ensayo, el siguiente trabajo era implementar la adaptación JNI:
creación/destrucción, espera, despertar, estado de espera y eventos de FD. Después
habrá que seguir resolviendo dependencias de ejecución (Binder, reloj, identidad,
trazas, Parcel/Bundle, utilidades y demás referencias que aparezcan). Haber llegado
al primer método native no demuestra que sean los únicos componentes pendientes.
Los algoritmos Java de ordenación/despacho deben seguir siendo los originales.

El runtime del contador y su ventana siguen usando las API propias previas y
sirven de regresión; no se han sustituido por estas clases todavía. La compilación
no acredita Activity/View originales, framework completo ni estabilidad de APK.
Las licencias y avisos de cada fuente/dependencia deberán conservarse al incorporar
y distribuir código original; actualmente se publica el manifiesto y herramientas,
no los archivos descargados ni el JAR de referencia.

## Enlace JNI ya probado

archtv-aosp-linux implementa los seis enlaces con epoll/eventfd. El conjunto de
fuentes original incluye ahora SparseArray, ContainerHelpers, ArrayUtils y
GrowingArrayUtils para ejecutar el listener público de FD. NativeQueueProbe pasa
en ART con una tubería Linux y despertar entre hilos. La prueba de despacho con
Handler falla todavía por ausencia de Parcelable. Ver docs/AOSP-JNI-LINUX.md y
reports/aosp-queue-jni/. Este avance no sustituye las API de la APK ni convierte
el conjunto completo en una cola Java funcional.

## Despacho y semántica originales

El conjunto actual contiene 19 fuentes originales, con Parcelable, relojes,
atribución de trabajo, Binder/Process y sus dependencias de inicialización.
Handler.post/Looper.loop y las pruebas de orden, diferidos, cancelación, barreras,
idle y cierre ya pasan sobre Linux local. Ver docs/AOSP-HANDLER-LINUX.md y
reports/aosp-handler-foundations/. La primera prueba ampliada tuvo un timeout no
diagnosticado; los diez procesos posteriores no acreditan estabilidad prolongada.
La APK, Activity/View y el resto de servicios siguen pendientes de integración/port.
