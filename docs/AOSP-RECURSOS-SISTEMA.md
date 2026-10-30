# Recursos de sistema AOSP junto a los del APK

build_system_resources.py construye un APK de recursos sin DEX, paquete android
(ID 0x01), con los 18 valores por defecto que ViewConfiguration original utiliza.
Se extraen las definiciones originales de config.xml; config.xml/dimens.xml y el
consumidor Java están fijados por tamaño/SHA-256 en framework-study.json. No se
cambian dimensiones, booleanos ni enteros y no se añade una política de producto
para evitar llamadas a servicios.

Los IDs privados se obtienen con javap de la referencia interna Android cuyo hash
ya fija la compilación del framework. Es importante usar la misma referencia:
esos IDs privados no son una API estable entre versiones. AAPT2 recibe stable-ids
y el builder comprueba los IDs emitidos. No copia clases ni bytecode de esa
referencia. Herramientas e inputs se vuelven a verificar antes de guardar la
procedencia final.

Este APK es un perfil parcial de valores por defecto. No es framework-res.apk
completo, no contiene temas, estilos ni todas las variantes por configuración.
No acredita compatibilidad general ni sustituye la inicialización global de
Resources.getSystem o AssetManager.getSystem.

## Construcción y carga explícita

```sh
python tools/apk/build_system_resources.py \
  --sources /home/tv/.cache/archtv/aosp-framework-study/pinned \
  --reference /home/tv/.cache/archtv/aosp-compile-tools/android-all-13.jar \
  --tools /home/tv/.cache/archtv/apk-build-tools --output dist/apk/system-new
python tools/apk/build_androidfw.py \
  --sources /home/tv/.cache/archtv/androidfw-port \
  --art /home/tv/.cache/archtv/art-host/host/art-13.0.0 \
  --reuse-archives dist/apk/androidfw-clang-1 --output dist/apk/androidfw-system-new
python tools/apk/probe_view_constructor.py \
  --aosp-build dist/apk/aosp-view-constructor-singleton-1 \
  --tools /home/tv/.cache/archtv/apk-build-tools \
  --art /home/tv/.cache/archtv/art-host/host/art-13.0.0 \
  --linux-library /home/tv/.cache/archtv/smithay/target/debug/libarchtv_aosp_linux.so \
  --resources-library dist/apk/androidfw-system-new/libarchtv_resources_linux.so \
  --system-resources-build dist/apk/system-new --output dist/apk/system-check-new
```

Los destinos deben ser nuevos. --reuse-archives es opcional: permite volver a
enlazar el probe y JNI sin recompilar las fuentes nativas originales. Verifica
fuentes, receta, compilador, libc++, comandos de compilación (exceptuando destino
-o) y hashes de todos los archivos .a de un build completo previo. No permite
combinarlo con --resume. Los controles negativos de hash/comando alterados se
rechazan antes de enlazar, conservados en reports/aosp-system-resources/.

ApkResources y AppEnvironment tienen una sobrecarga con ruta explícita al APK de
sistema. Cargan primero ese asset con PROPERTY_SYSTEM original y después el APK de
aplicación. El JNI acepta únicamente flags 0 o PROPERTY_SYSTEM y pasa el flag a
ApkAssets::Load original; el resto sigue fallando expresamente. El AssetManager2
original conserva ambos assets. Se cierran manager y handles de ambos APK también
en los caminos de fallo, manteniendo los errores originales como causa.

La llamada existente de dos argumentos a AppEnvironment sigue cargando sólo el
APK. La carga del perfil se prueba con la opción explícita del comprobador, que
verifica su hash antes de invocar ART. La selección/instalación del perfil por el
anfitrión de producción y su política de confianza siguen pendientes.

## Evidencia y frontera siguiente

SystemResourcesChecks verifica los 18 recursos por nombre, los IDs del paquete
android y cookie 1; comprueba dimensiones dp/mm y float, booleanos y enteros a
160/320 dpi. También verifica config_scrollbarSize=0x010500d6, que la cadena del
contador sigue en el paquete 0x7f/cookie 2, y el rechazo de flags no soportados.
Restaura la configuración inicial antes de intentar el constructor. Cambiar la
densidad en Resources no acredita HiDPI Wayland ni selección de qualifiers.

El constructor original de View supera ahora el recurso ausente y llega a
WindowManagerGlobal, aún sin portar. config_overrideHasPermanentMenuKey conserva
el valor AOSP 0: solicita el servicio de ventanas para detectar la barra de
navegación. No se ha evitado esa dependencia mediante un valor inventado.
original_view_constructed sigue siendo false; dibujo, RenderNode y el port de la
interfaz original siguen abiertos.

Pasan además la regresión completa del contador con los nuevos adaptadores/JNI y
la APK independiente de métricas. Logs, hashes y procedencia están en
reports/aosp-system-resources/. Los recursos siguen sin firma y no se afirma una
instalación ni una distribución terminadas.
