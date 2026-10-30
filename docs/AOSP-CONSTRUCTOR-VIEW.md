# Constructor original de View con recursos del APK

probe_view_constructor.py compila un DEX aislado con los adaptadores Linux
existentes (LinuxContext, AppEnvironment, ApkResources, HostProfile y preferencias
enteras). No incluye las View, ViewGroup, Activity o widgets propios del prototipo,
ni clases de aplicación. El otro DEX contiene las fuentes originales de AOSP
compiladas. La referencia completa Android sólo se usa al compilar.

ViewConstructorProbe ejecuta new View(context), con Application original enlazada
al contexto Linux, Resources original cargado desde la APK dorada del contador y
Looper principal original. Antes de intentarlo comprueba el Looper y la cadena
Contador: del APK. No utiliza Unsafe, no omite inicializadores y no captura
AssertionError como resultado válido.

```sh
python tools/apk/build_aosp_queue.py --with-views \
  --sources /home/tv/.cache/archtv/aosp-framework-study/pinned \
  --reference /home/tv/.cache/archtv/aosp-compile-tools/android-all-13.jar \
  --tools /home/tv/.cache/archtv/apk-build-tools --output dist/apk/views-constructor-new
python tools/apk/probe_view_constructor.py --aosp-build dist/apk/views-constructor-new \
  --tools /home/tv/.cache/archtv/apk-build-tools \
  --art /home/tv/.cache/archtv/art-host/host/art-13.0.0 \
  --linux-library /home/tv/.cache/archtv/smithay/target/debug/libarchtv_aosp_linux.so \
  --resources-library dist/apk/androidfw-clang-1/libarchtv_resources_linux.so \
  --output dist/apk/view-constructor-check-new
```

Los destinos deben ser nuevos. El diagnóstico distingue diagnostic_completed de
original_view_constructed: el primero sólo confirma que se ejecutó y cerró
ordenadamente el ensayo. Un fallo de enlace o servicio ausente queda registrado
con su traza, sin declararse construcción de View satisfactoria.

## Fronteras observadas

La primera ejecución entra en View.<init> y falla en ViewOutlineProvider. Se
incorporan esa clase, InputEventConsistencyVerifier y ViewConfiguration originales.
La siguiente llega a ViewConfiguration.get y encuentra StrictMode ausente.
Al incorporar StrictMode original se alcanza su inicializador, que necesita Log.
También se añade SparseLongArray, utilizado por los estados originales de
StrictMode. Fuentes y hashes quedan fijados en framework-study.json; no se cambian
sus implementaciones por equivalentes simplificados.

reports/aosp-view-constructor/ conserva los ensayos y la procedencia del conjunto
final. Los fallos intermedios pertenecen a builds distintos y sus hashes lo
reflejan; no se presentan como resultados de la misma compilación.

## Trabajo posterior

Resolver el enlace nativo y las dependencias restantes del constructor. La lectura
de ViewConfiguration original muestra además recursos internos de dimensiones,
booleanos y enteros, y una ruta al servicio de ventanas según configuración del
producto. View requiere RenderNode y su frontera gráfica nativa. Estas rutas
necesitan implementaciones reales y recursos de sistema; no basta con inicializar
las clases o ejecutar helpers estáticos.

La prueba utiliza el contexto Application existente; todavía no acredita un
contexto visual completo, aislamiento, metadatos de paquete, temas, servicios,
dibujo o entrada. Tampoco sustituye el runtime de las APK que conserva su interfaz
propia como regresión. La API de preferencias de enteros del DEX adaptador sigue
siendo la del prototipo y se registra expresamente.


## Frontera final registrada

El conjunto de 73 fuentes Java originales sigue pasando la inicialización de
View/ViewGroup/ContextThemeWrapper, StateSet y helpers de medida. El constructor
avanza hasta StrictMode.<clinit> → Log.isLoggable, donde ART lanza
UnsatisfiedLinkError por JNI aún ausente. stage-4/result.json registra
original_view_constructed=false. El siguiente trabajo es el enlace nativo de
registro sobre Linux; todavía no se han alcanzado las rutas de recursos internos
y RenderNode mencionadas arriba.
