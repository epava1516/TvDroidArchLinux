# Log original de AOSP con JNI Linux

android.util.Log.java permanece original, fijado en framework-study.json. El
módulo Rust logging de archtv-aosp-linux proporciona sus tres enlaces nativos:
isLoggable, println_native y logger_entry_max_payload_native. No se modifica el
Java para evitar StrictMode ni se devuelve éxito sin escribir.

## Backend y límites

Los mensajes se escriben en stderr con el prefijo ANDROID_LOG, canal, prioridad
y etiqueta. main/radio/system/crash son etiquetas del mismo flujo Linux, no
buffers Android independientes. El supervisor existente puede conservar ese
stderr. No hay logd, ring buffer, adb logcat ni transporte binario de eventos.
println_native rechaza otros buffers con -EOPNOTSUPP y prioridades fuera de 2–7
con -EINVAL. Un mensaje filtrado devuelve -EPERM; uno escrito devuelve sus bytes
UTF-8 aceptados. Los errores de escritura propagan una excepción Java mediante el
guard JNI existente, sin convertirlos en éxito.

El nivel por defecto es INFO. Se consulta el perfil de propiedades de proceso
ARCHTV_ANDROID_PROPERTY_ con esta precedencia:

1. log.tag.<etiqueta>
2. persist.log.tag.<etiqueta>
3. log.tag
4. persist.log.tag

Se aceptan V/VERBOSE, D/DEBUG, I/INFO, W/WARN, E/ERROR, A/ASSERT y S/SILENT, sin
distinguir mayúsculas. Un valor ausente/inválido permite consultar el siguiente.
Estas variables no son un servicio global/persistente de propiedades Android.

Los String pasan por JNI UTF-16 a UTF-8 Linux; los sustitutos UTF-16 aislados se
reemplazan. Se aceptan etiquetas nulas/vacías y se escapan al imprimir el prefijo.
Los mensajes nulos lanzan NullPointerException. El presupuesto de payload es
4068 bytes, descontando etiqueta, prioridad y terminadores; el mensaje se trunca
en una frontera UTF-8 válida. Una etiqueta que supera el presupuesto devuelve
-E2BIG. Cada entrada utiliza el lock de stderr y puede sufrir la contrapresión
del destino; no es un backend asíncrono ni una prueba de latencia/estabilidad.

WTF y los helpers Java de Throwable necesitan otras dependencias originales y no
se dan por portados. Tampoco se ha verificado toda la política de StrictMode.

## Comprobación

```sh
CARGO_TARGET_DIR=/home/tv/.cache/archtv/smithay/target CARGO_BUILD_JOBS=1 \
  cargo build -p archtv-aosp-linux
python tools/apk/verify_linux_log.py \
  --aosp-build dist/apk/aosp-view-constructor-log-1 \
  --tools /home/tv/.cache/archtv/apk-build-tools \
  --art /home/tv/.cache/archtv/art-host/host/art-13.0.0 \
  --linux-library /home/tv/.cache/archtv/smithay/target/debug/libarchtv_aosp_linux.so \
  --output dist/apk/log-check-new
```

El build de framework debe incluir Log original (--with-views actualmente). El
verificador comprueba hashes, compila un DEX de prueba separado y confirma que
sólo contiene LogProbe. Ejecuta cuatro procesos ART con -Xcheck:jni: valores por
defecto, etiqueta DEBUG sobre global WARN, fallback persistente ERROR con valor
inválido previo, y global SILENT. Comprueba tanto resultados Java como bytes
reales de stderr: Unicode, truncación, canales, filtrado y mensajes rechazados.
No carga la referencia completa al ejecutar.

reports/aosp-linux-log/ conserva logs, comandos y hashes. Los cinco tests Rust
pasan en el host; los tests de sockets de la cola requieren ejecutarse fuera del
sandbox que devuelve EPERM en sus descriptores sintéticos. También pasa la
regresión completa headless del contador con la nueva biblioteca JNI.
