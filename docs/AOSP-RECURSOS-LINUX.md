# Port nativo de recursos de AOSP a Linux

El objetivo es reutilizar `libandroidfw` original como proveedor de recursos de
las APK, sustituyendo progresivamente el lector reducido propio. La biblioteca ya se conecta con las clases originales `AssetManager`,
`ApkAssets` y `StringBlock` en ART. Sigue pendiente integrar `Resources`, la
inicialización pública de recursos del sistema. La APK del contador ya usa este proveedor.

## Fuentes y construcción

`runtime/aosp/androidfw-sources.json` fija revisiones Android 13, subárboles y
SHA-256 de cada archivo. Los archivos originales se descargan en caché y se
verifican antes de compilar. Los hashes de los archivos son la referencia:
Gitiles puede variar las marcas de tiempo del contenedor tar.

Se utiliza Clang, las cabeceras originales de libc++ y la biblioteca libc++.so
incluida en el bundle ART del laboratorio. No se mezclan las cabeceras de
libstdc++ con esa ABI. La construcción secuencial limita el consumo de la VM.
`NDEBUG` coincide con la configuración global de Soong. Las selecciones de
fuentes y cabeceras se registran en `androidfw-build.json`.

```sh
python tools/apk/fetch_androidfw_sources.py /home/tv/.cache/archtv/androidfw-port
python tools/apk/build_androidfw.py \
  --sources /home/tv/.cache/archtv/androidfw-port \
  --art /home/tv/.cache/archtv/art-host/host/art-13.0.0 \
  --output dist/apk/androidfw-native
python tools/apk/verify_androidfw.py \
  --build dist/apk/androidfw-native --output dist/apk/androidfw-check
```

La salida debe ser nueva. `--resume` reutiliza objetos verificados después de
un fallo terminal; un proceso todavía activo no debe relanzarse.

La receta genera archivos estáticos, siguiendo la selección host de AOSP.
`CursorWindow` se compila con cabeceras Binder; la herramienta de recursos no
selecciona ese objeto al enlazar. Esto no implementa Binder IPC ni prueba que
CursorWindow pueda utilizarse.

## Comprobación y límites

`archtv-resource-probe` llama a `AssetManager`, `ResTable` y al pool de cadenas
originales para abrir una APK y resolver nombres, valores y referencias. El
adaptador propio únicamente transforma argumentos y escribe resultados.

El verificador exige el hash de la APK del contador, compara tres textos y
comprueba que cambiar los recursos sin cambiar `classes.dex` cambia la lectura.
También exige errores sin señal ni timeout ante un nombre ausente, una APK
inexistente y una tabla truncada. Los artefactos modificados son pruebas sin
firma válida; no acreditan verificación de firma o instalación.

La ejecución de esta herramienta no sustituye todavía el proveedor Java del
contador. Faltan el puente JNI, configuración/idiomas, temas, recursos de sistema,
pruebas ampliadas de formatos y las clases originales de interfaz. Tampoco
acredita aislamiento frente a APK hostiles, estabilidad prolongada ni soporte
general de aplicaciones. No requiere iniciar Waydroid ni un sistema Android.

## Puente JNI sobre ART

`runtime/aosp/native/resources-jni.cpp` adapta once entradas JNI de las clases
originales. El análisis y la selección de recursos se delegan en `ApkAssets`,
`AssetManager2` y `ResStringPool` originales. Los identificadores nativos son
handles comprobados bajo mutex; el gestor conserva referencias a sus APK para
mantener vivos sus datos. Las cadenas se devuelven mediante JNI UTF-16.

El conjunto Java ampliado contiene 30 fuentes originales sin modificar,
incluidas las dependencias de inicialización de `ActivityInfo` y sus colecciones.
El JAR de referencia solo sirve al compilador; no forma parte del classpath ART.

```sh
python tools/apk/build_aosp_queue.py --with-resources \
  --sources /home/tv/.cache/archtv/aosp-framework-study/pinned \
  --reference /home/tv/.cache/archtv/aosp-compile-tools/android-all-13.jar \
  --tools /home/tv/.cache/archtv/apk-build-tools \
  --output dist/apk/aosp-resources-java
python tools/apk/verify_resources_jni.py \
  --art /home/tv/.cache/archtv/art-host/host/art-13.0.0 \
  --java-build dist/apk/aosp-resources-java \
  --native-build dist/apk/androidfw-native \
  --output dist/apk/aosp-resources-jni
```

Pasan dos procesos ART con la APK original, la variante del mismo DEX y los
rechazos de tabla truncada y ruta inexistente, con `-Xcheck:jni` activo. Se prueban
identificadores con nombre completo y valores de tipo/paquete por defecto,
`AssetManager.getResourceText`, la caché original de cadenas y el cierre del gestor.
Las pruebas están en `reports/aosp-resources-jni/`.

El comprobador usa por reflexión el constructor interno empleado por el Builder
de AOSP y su instalación nativa de APK. Así aísla la inicialización del sistema,
que todavía presupone `framework-res.apk` y overlays. No acredita el constructor
público, ni `Resources.getString`, ni el proveedor de la APK del contador. Las
entradas no portadas fallan por enlace ausente; formatos distintos de APK normal,
flags especiales, proveedores y cadenas con estilos se rechazan explícitamente.
El código Java completo de `Parcelling` compila, pero sus operaciones Parcel no
se han habilitado ni probado.

## Integración en el contador

`ApkResources` ya no interpreta el formato binario. Conserva la validación del
presupuesto ZIP de 16 MiB y adapta la inicialización interna del gestor original;
`getString` llama a `AssetManager.getResourceText`. No hay un lector propio de
respaldo. Main carga explícitamente la biblioteca de recursos y cierra el gestor
y sus ApkAssets en `finally` después de la UI. Activity/View siguen siendo propios.

El runtime requiere framework.jar construido con `--with-resources`. Main exige
`-Darchtv.resources.library`; el cliente Rust recibe la ruta mediante
`ARCHTV_APK_RESOURCES_LIBRARY`. `verify_counter_headless.py` usa
`--resources-library`, además de los argumentos existentes. La biblioteca se genera
junto con la herramienta nativa de recursos.

Pasan la APK original, persistencia 0→1→2/reapertura 2→3, ráfaga, EOF, error de
comando y recuperación, exclusión de datos, variante con el mismo DEX y rechazos
de tablas truncadas/preferencias corruptas. En DRM/Pixman 720p pasan las dos
sesiones, entrada uinput y coincidencia exacta RGB entre frame y scanout.
Las evidencias están en `reports/aosp-resources-headless/` y
`reports/aosp-resources-wayland/`; ambas exigen la traza de inicialización AOSP y
registran hashes del DEX y la biblioteca. Esto sustituye el parser del contador;
no completa `Resources`, los recursos de sistema ni el port de interfaz.
