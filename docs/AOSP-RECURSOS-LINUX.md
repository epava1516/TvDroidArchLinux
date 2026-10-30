# Port nativo de recursos de AOSP a Linux

El objetivo es reutilizar `libandroidfw` original como proveedor de recursos de
las APK, sustituyendo progresivamente el lector reducido propio. Este primer
paso construye la biblioteca y una herramienta de comprobación; todavía no
conecta las clases Java originales `Resources` y `AssetManager` con ART.

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
