# Skia original para HWUI host

La variante host CPU del Skia original fijado en `hwui-sources.json` ya compila
y supera una prueba de dibujo y lectura exacta de píxeles. Es una dependencia
para enlazar HWUI/RenderNode; su ejecución gráfica en ART y presentación Wayland
siguen pendientes.

## Fuentes y herramientas

`skia-extra-sources.json` fija DNG SDK, Piex y Wuffs en las revisiones declaradas
por el DEPS original de Skia. El descargador común verifica sus archivos igual
que los árboles HWUI. `skia-gn-tool.json` fija el ZIP y el ejecutable GN cuya
revisión aparece en el script original `bin/fetch-gn`.

El manifiesto adicional incluye también las cabeceras Bionic de Android 13,
fijadas a 0b981d1ec055efaef86d8a5d402cf1b3167ba10b. De ese árbol se exporta
únicamente stdatomic.h al perfil C++ generado. No se introduce su directorio
libc/include completo en las rutas de búsqueda de una construcción glibc.

Se instaló Ninja 1.13.2-3 con pacman. El constructor registra versiones de Clang,
Ninja y paquetes de códecs/fuentes del anfitrión. Las interfaces C de estos
últimos se enlazan con bibliotecas Linux; esto no acredita una construcción
hermética ni sustituye la futura revisión de licencias y empaquetado.

```sh
python tools/apk/fetch_skia_gn.py /home/tv/.cache/archtv/hwui-tools
python tools/apk/fetch_androidfw_sources.py \
  /home/tv/.cache/archtv/hwui-port/skia/third_party/externals \
  --manifest runtime/aosp/skia-extra-sources.json
python tools/apk/build_skia_host.py \
  --sources /home/tv/.cache/archtv/hwui-port \
  --androidfw-sources /home/tv/.cache/archtv/androidfw-port \
  --gn /home/tv/.cache/archtv/hwui-tools/gn \
  --output dist/apk/skia-host-build
```

El constructor verifica los tres manifiestos de fuentes antes de generar Ninja.
Extrae únicamente la función `generate_args` de gn_to_bp.py, ya verificada, y
reutiliza sus argumentos host Linux originales. Añade arquitectura x64, Clang,
PIC, O1, las rutas de configuración Linux y las cabeceras libc++ usadas por ART.
El perfil original host desactiva GPU: esta fase estudia el rasterizado CPU; la
aceleración y los objetivos de rendimiento del roadmap siguen pendientes.

La compilación usa un solo trabajo. Una reanudación con `--resume` exige la
misma configuración, manifiestos, herramientas y paquetes. No debe invocarse
mientras otra compilación del mismo directorio siga activa. El archivo
result.json registra el resultado terminal y los hashes de archivos estáticos;
la existencia del directorio o de configuration.json no demuestra éxito.

## Compatibilidad Clang 23 sin desactivar SIMD

El primer intento alcanzó 120 tareas antes de fallar en el builtin
`__builtin_ia32_vcvtph2ps256`, retirado de Clang 23. Las fuentes originales
permanecen intactas. `skcms-clang-compat.h` adapta esa llamada al intrinsic público
`_mm256_cvtph_ps`, con el cast del vector de entrada. Conserva la conversión F16C
y el despacho original por capacidad de CPU; no activa AVX2 en todo el programa.

La prueba `verify_skcms_compat.py` ejecuta la conversión en una CPU con AVX2/F16C
y compara los 65 536 patrones binarios de half contra una referencia escalar
IEEE, bit a bit. Incluye subnormales, ceros con signo, infinitos y NaN con sus
payloads y quiet bit. Una CPU sin esas capacidades sale con 77 y no acredita la
prueba. En esta VM pasó con Clang 23.1.4:

```sh
python tools/apk/verify_skcms_compat.py --output dist/apk/skcms-compat-check
```

`reports/aosp-skia-host/` conserva el fallo original, las pruebas numéricas, la
descarga GN desde una caché nueva y rechazos de binario modificado y de
reanudación con distinta configuración. Esas pruebas previas no acreditaban aún
una construcción Skia terminada; el resultado posterior se registra abajo.

La comprobación numérica del intrinsic por sí sola no acredita Canvas ni HWUI.
El resultado posterior de Canvas se describe abajo; el enlace HWUI y la
integración CriticalNative de RenderNode siguen pendientes.

El intento con la adaptación F16C superó ese error y se detuvo después en
SkATrace.cpp: cutils/trace.h introducía macros atómicas C de Clang antes de
`<atomic>` del libc++ original de ART. La cabecera stdatomic.h original de Bionic
usa la implementación C++ `<atomic>` y exporta sus nombres. Con esa cabecera
intacta, SkATrace.cpp ya compila como objeto. El constructor registra su hash y
la aplica solo a C++; los archivos C conservan stdatomic del anfitrión. Con este
perfil, skia-host-6 termina sus 645 tareas y genera libskia.a, libdng_sdk.a,
libpiex.a y libwuffs.a. Ver reports/aosp-skia-host/atomic-headers/ y el resultado
terminal en reports/aosp-skia-raster/build/.

## Dibujo nativo verificado

`skia-raster-probe.cpp` y `verify_skia_raster.py` ya enlazan y ejecutan las
bibliotecas construidas. El verificador exige un resultado Skia exitoso y
archivos estáticos con hashes coincidentes antes del enlace, y comprueba el
libc++ de ART contra el de los archivos androidfw usados como apoyo.

```sh
python tools/apk/verify_skia_raster.py \
  --skia-build dist/apk/skia-host-6 \
  --sources /home/tv/.cache/archtv/hwui-port \
  --androidfw-build dist/apk/androidfw-clang-1 \
  --androidfw-sources /home/tv/.cache/archtv/androidfw-port \
  --art /home/tv/.cache/archtv/art-host/host/art-13.0.0 \
  --output dist/apk/skia-raster-check
```

La prueba utiliza SkSurface y SkCanvas originales, limpia el fondo, dibuja un
rectángulo rojo y otro azul con recorte y traslación, y comprueba los 3072
píxeles por peekPixels/getColor y por readPixels RGBA. Coinciden ambas rutas.
El archivo PPM resultante contiene 2304 píxeles de fondo, 732 rojos y 36 azules,
comprobados también desde Python. No hay fuentes ni texto en esta prueba.

`reports/aosp-skia-raster/` conserva configuración, logs, hashes, comandos,
resultado terminal y PPM. Las fuentes originales se verificaron de nuevo tras
terminar la construcción. Los archivos ar son completos, no referencias a
objetos externos. El dibujo es un ejecutable C++ fuera de ART: no acredita
Canvas Java, View, RenderNode, GPU, ventanas Wayland ni las metas de rendimiento
o estabilidad de la distribución.
