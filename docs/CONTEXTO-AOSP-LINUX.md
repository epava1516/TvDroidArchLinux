# Context y Application originales sobre Linux

El runtime ya incorpora Context, ContextWrapper y Application originales de AOSP
Android 13. Se retiró runtime/apk/java/android/content/Context.java, que sólo
contenía getString y preferencias. getString/getText ahora ejecutan los métodos
concretos originales de Context y Resources.

El conjunto --with-context conserva 54 fuentes originales sin modificar y los
cuatro bindings sysprop precompilados ya documentados. Esto no porta ContextImpl,
ActivityThread ni los servicios de Android.

## Límite de servicios Linux

LinuxContext extiende el Context abstracto original. Su archivo se genera desde
las declaraciones del framework.jar verificado y se comprueba con --check.
Hay 132 métodos abstractos: seis delegan en estado real; los otros 126 lanzan
UnsupportedOperationException con el nombre de la API. No devuelven valores de
éxito o servicios simulados. Los demás métodos concretos siguen siendo originales;
las dependencias y tipos aún no portados pueden producir errores de enlace,
incluso antes de entrar en un hook.

| Método abstracto soportado | Implementación actual |
| --- | --- |
| getResources | Resources original del APK; lectura de cadenas y métricas verificadas |
| getAssets | El AssetManager original ya abierto; no acredita todos sus métodos de archivos/XML |
| getSharedPreferences(String,int) | Backend existente de enteros, sólo MODE_PRIVATE; no SharedPreferencesImpl/XML de Android |
| getClassLoader | Classloader real del proceso que contiene runtime y APK; no aislamiento por aplicación |
| getMainLooper | Principal original preparado por el anfitrión |
| getApplicationContext | Instancia real de Application original, única en el proceso |

Application se construye con su controlador original de ComponentCallbacks y se
conecta al contexto Linux mediante attachBaseContext original de ContextWrapper.
No se llama Application.attach, que depende de ContextImpl/LoadedApk. Ese estado
y los metadatos de paquete todavía no están implementados. El host invoca onCreate
en main antes de crear la Activity y envía onConfigurationChanged después de
actualizar Resources en el Handler UI.

Se utiliza Application por defecto. Aún no se descubre ni instancia una subclase
Application declarada en AndroidManifest.xml. Tampoco se han conectado los
ActivityLifecycleCallbacks a la Activity propia ni señales reales de presión de
memoria Linux. Las pruebas de memoria despachan callbacks manualmente; no simulan
una integración de sistema ya terminada. No se invoca onTerminate al cerrar.

## Construcción y pruebas

```sh
python tools/apk/build_aosp_queue.py --with-context \
  --sources /home/tv/.cache/archtv/aosp-framework-study/pinned \
  --reference /home/tv/.cache/archtv/aosp-compile-tools/android-all-13.jar \
  --tools /home/tv/.cache/archtv/apk-build-tools \
  --output dist/apk/context-framework
python tools/apk/generate_linux_context.py --aosp-build dist/apk/context-framework \
  --output runtime/apk/java/org/archtv/apkruntime/LinuxContext.java --check
python tools/apk/build_apk_runtime.py --aosp-build dist/apk/context-framework \
  --tools /home/tv/.cache/archtv/apk-build-tools --output dist/apk/context-runtime
```

Los destinos de build deben ser nuevos. generate_linux_context.py sin --check
crea un archivo nuevo: los cambios de soporte se revisan en el generador, no
mediante edición manual del resultado. El runtime verifica también el JAR interno
usado al compilar las firmas ocultas; no incorpora la referencia completa.

verify_context.py construye un DEX de comprobación separado. Comprueba Resources/
AssetManager compartidos, getText/getString originales, Application real,
classloader de la APK, Looper principal, preferencias, attach único de
ContextWrapper, callbacks de configuración/memoria y unregister. Una solicitud de
servicio window falla explícitamente. Los comprobadores no entran en el DEX del
runtime ni se recompila la APK dorada.

Las evidencias están en reports/aosp-context-probe/, aosp-context-headless/,
aosp-context-wayland/ y aosp-context-wayland-resize/. Se conservan la regresión
completa del contador, dos sesiones DRM/Pixman 720p con entrada/persistencia y RGB
idéntico, y el resize Wayland anidado después del primer frame.

## Pendientes

Faltan los servicios del contexto, paquete/manifiesto, permisos y aislamiento,
ContextImpl/LoadedApk, recursos de sistema, SharedPreferencesImpl y la jerarquía
original de Activity/View. La Activity sigue siendo el subconjunto propio y ahora
hereda LinuxContext/Context originales. Este hito no acredita compatibilidad
general, estabilidad prolongada, instalación final o distribución.

## Segunda APK independiente

fixtures/apk/context-metrics prueba estas rutas desde una aplicación compilada
sólo contra el SDK público, sin código del anfitrión ni clases de aplicación en
el DEX del runtime. Comprueba Application real, recursos compartidos y nombre de
su propio APK, callbacks en el Looper principal, dimensiones dp y orientación.
El texto visible lo actualiza la aplicación desde ComponentCallbacks2.

reports/aosp-context-metrics/ conserva inventario/procedencia y dos pruebas:
ART 1280×720 → 1920×1080 → 1080×1920 con callbacks 0→1→2; Wayland real
960×540 → 800×450 con callbacks 0→1 y buffers PNG de ambos tamaños. La prueba
Wayland usa el compositor propio anidado en Weston headless; no acredita un
cambio de modo DRM ni sustituye las pruebas nativas del contador.
