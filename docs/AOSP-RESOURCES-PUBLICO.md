# Resources original sobre Linux

El constructor público `Resources(AssetManager, DisplayMetrics, Configuration)`
ya funciona en ART junto con `getIdentifier` y `getString` originales. El conjunto
ampliado conserva 48 fuentes Java de AOSP Android 13 sin modificar. Incluye
ResourcesImpl, configuración, métricas, cachés, LocaleList, TextUtils y Build.
El contador integrado ya llama a Resources.getString. HostProfile configura
explícitamente el perfil de arranque antes de inicializar Build y Resources.

## Procedencia y construcción

`framework-study.json` fija las fuentes y el grupo `public_resources_sources`.
El constructor ofrece tres conjuntos: el predeterminado de cola/Handler (19
fuentes), `--with-resources` (30) y `--with-public-resources` (48).

Hay una excepción explícita a la referencia usada sólo para compilar:
`prebuilt-bindings.json` autoriza cuatro clases generadas `android.sysprop` del
artefacto Android 13 ya verificado: DisplayProperties, SocProperties,
TelephonyProperties y DeviceProperties. Se comprueban el hash del JAR y los
bytes/hash de cada clase antes de incorporarlas. No se carga el JAR completo,
ni el runner de Robolectric, sus comprobadores o shadows. Reconstruir estas cuatro clases con
el generador oficial sysprop continúa pendiente; no son fuentes recompiladas
por esta receta. Los getters no habilitan servicios telefónicos o de hardware.

La declaración auxiliar `java.lang.ref.Reference` sólo permite compilar la llamada
`refersTo`: se excluye del JAR de framework y del DEX. Se verifica por reflexión
que el ART real ofrece el método y distingue el referente de otro objeto. Las
otras declaraciones de compilación tampoco se incorporan al runtime.

```sh
python tools/apk/build_aosp_queue.py --with-public-resources \
  --sources /home/tv/.cache/archtv/aosp-framework-study/pinned \
  --reference /home/tv/.cache/archtv/aosp-compile-tools/android-all-13.jar \
  --tools /home/tv/.cache/archtv/apk-build-tools \
  --output dist/apk/public-resources
python tools/apk/probe_public_resources.py \
  --art /home/tv/.cache/archtv/art-host/host/art-13.0.0 \
  --java-build dist/apk/public-resources \
  --linux-library /home/tv/.cache/archtv/smithay/target/debug/libarchtv_aosp_linux.so \
  --resources-library dist/apk/androidfw-native/libarchtv_resources_linux.so \
  --output dist/apk/public-resources-proof
```

Las bibliotecas deben reconstruirse con las recetas nativas de
AOSP-JNI-LINUX.md y AOSP-RECURSOS-LINUX.md. Los directorios de salida deben ser
nuevos. El manifiesto ampliado se descarga con `study_framework.py --fetch`.

## Adaptaciones Linux

El JNI convierte la configuración Java al `ResTable_config` original y llama a
AssetManager2.SetConfiguration, incluido locale BCP-47, densidad, dimensiones,
SDK y el bit de pantalla redonda. La selección de recursos continúa en AOSP.
Se ofrece el callback real de destrucción de Theme para NativeAllocationRegistry,
además de creación nativa. No se acredita el sistema de estilos o temas completo.

SystemProperties admite lecturas de cadenas UTF-16, enteros decimales y booleanos
con los valores de libbase ParseBool. Son variables de entorno del proceso con
prefijo `ARCHTV_ANDROID_PROPERTY_`, no un servicio global Android. Valores vacíos o
ausentes usan el valor por defecto; no hay mutación, callbacks ni handles.
Trace informa cero tags habilitados porque el host no tiene un colector configurado;
no se implementa emisión ni activación de trazas.

El comprobador declara un perfil de laboratorio x86_64/API 33 y registra sus
propiedades en el resultado. Describe el ART y las fuentes seleccionadas; no
acredita compatibilidad completa API 33 ni carga de bibliotecas NDK/Bionic.

## Evidencia y límites

`reports/aosp-public-resources/` conserva compilación y ejecución con `-Xcheck:jni`.
La prueba verifica el constructor público, texto por identificador, ausencia con
NotFoundException, dimensiones 1280×720, cambio a densidad 240/fontScale 1.25,
dirección RTL para árabe y conservación del texto por defecto. No hay todavía
una fixture con traducciones o calificadores para probar su selección.

También comprueba propiedades Unicode con un carácter suplementario, defaults,
booleanos inválidos, trazas desactivadas y la llamada real de liberación de Theme
mediante NativeAllocationRegistry. Esto no prueba finalización por GC. La
regresión separada de recursos y la de relojes/Handler/colas se conservan junto
con el hito; las diez ejecuciones de semántica no son una prueba de estabilidad.

AssetManager sigue inicializándose por su constructor interno, sin
framework-res.apk, overlays o zygote. No funciona aún la inicialización pública de
recursos del sistema, Resources.getSystem ni la integración general de Activity,
View, estilos y gráficos originales. Tampoco se cierran aislamiento, compatibilidad
de APK ampliada, H7 o distribución.

## Integración y perfil del contador

Main inicializa `HostProfile` una sola vez mediante el adaptador Rust. El perfil
fija `ro.build.version.sdk=33`, `ro.build.version.release=13`, codename y
all_codenames a `REL`, y las listas ABI del proceso a `x86_64`. Se rechaza una
segunda inicialización o una arquitectura distinta a la verificada. Estos seis
valores tienen prioridad sobre las variables de entorno; las demás propiedades
siguen el proveedor de sólo lectura existente. No se habilita SystemProperties.set
ni un servidor de propiedades Android.

ApkResources construye Resources original y llama directamente a getString;
la reflexión queda limitada a inicializar el AssetManager interno sin recursos
de sistema. El tamaño inicial procede del configure Wayland y los cambios se envían al
Handler UI; la escala de superficie sigue siendo 1. El cierre conserva la
liberación de AssetManager/ApkAssets en finally.

Pasan el contador original, cierre/reapertura, persistencia, ráfaga, EOF, error y
recuperación, tabla truncada, preferencias corruptas y variante con el mismo DEX.
Una prueba con SDK/ABI contradictorios en el entorno conserva el perfil fijado.
Dos sesiones DRM/Pixman pasan entrada uinput y coincidencia exacta RGB de capturas.
Evidencia: reports/aosp-public-resources-headless/ y
reports/aosp-public-resources-wayland/. Esto no completa recursos de sistema,
Activity/View, estilos, Bionic/NDK, aislamiento ni estabilidad prolongada.

Las métricas iniciales ya proceden de la ventana Wayland; el runtime acepta
cambios de tamaño en el hilo UI original. Ver AOSP-METRICAS-WAYLAND.md para las pruebas y sus límites.
