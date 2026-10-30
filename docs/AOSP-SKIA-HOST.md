# Skia original para HWUI host

El enlace de RenderNode necesita Skia y el resto de HWUI. Este avance prepara la
construcción del Skia original fijado en `hwui-sources.json`; todavía no acredita
una biblioteca Skia completa, ejecución gráfica en ART ni presentación Wayland.

## Fuentes y herramientas

`skia-extra-sources.json` fija DNG SDK, Piex y Wuffs en las revisiones declaradas
por el DEPS original de Skia. El descargador común verifica sus archivos igual
que los árboles HWUI. `skia-gn-tool.json` fija el ZIP y el ejecutable GN cuya
revisión aparece en el script original `bin/fetch-gn`.

Se instaló Ninja 1.13.2-3 con pacman. El constructor registra versiones de Clang,
Ninja y paquetes de códecs/fuentes del anfitrión. Las interfaces C de estos
últimos se enlazarán con bibliotecas Linux; esto no acredita una construcción
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
reanudación con distinta configuración. La compilación con la adaptación debe
completar todavía sus 645 tareas antes de acreditar un Skia host construido.

Después se necesita una prueba real de Canvas y lectura de píxeles, el enlace de
HWUI y la adaptación CriticalNative descrita en AOSP-RENDERNODE-NATIVO.md. Ninguna
de esas fases queda superada por la comprobación numérica del intrinsic.

Se prepararon `skia-raster-probe.cpp` y `verify_skia_raster.py` para ese siguiente
paso: dibujan rectángulos con recorte y traslación y comprueban 3072 píxeles y su
lectura RGBA. La fuente C++ supera sintaxis, pero la prueba no se ha enlazado ni
ejecutado todavía. El verificador exige un resultado Skia exitoso y archivos
estáticos con hashes coincidentes antes de intentar el enlace.
