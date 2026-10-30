# Adaptación tipada de CriticalNative a funciones host HWUI

El HWUI original incluye JNIEnv/jclass en las funciones CRITICAL_JNI_PARAMS de
host; ART llama a métodos Java CriticalNative con parámetros primitivos sin esos
dos argumentos. Registrar directamente el puntero host no respeta esa ABI.

`runtime/aosp/native/critical-host-adapter.h` genera una entrada de la firma
primitiva que llama a la función host original con los dos argumentos de
contexto nulos. La adaptación de registros y pila la genera C++ a partir del
tipo de la función. Debe utilizarse únicamente con funciones host cuyos dos
parámetros de contexto no se usan, como los parámetros anónimos de la macro
original. No adapta funciones JNI normales que necesitan JNIEnv o jclass.

El adaptador admite retornos JNI primitivos o void y rechaza referencias a
objetos en los argumentos. No cambia el código Java, las anotaciones ni el
cuerpo de la función host que se envuelva.

## Prueba ART

`fixtures/aosp-critical-host/` define ocho firmas propias para probar la ABI,
sin proporcionar clases Android ni reemplazar una implementación gráfica.
`verify_critical_host.py` verifica la cabecera JNI original, las cabeceras libc++
y la referencia de compilación. El JAR de referencia solo se usa para javac;
la ejecución ART lleva únicamente el DEX de la prueba.

```sh
python tools/apk/verify_critical_host.py \
  --sources /home/tv/.cache/archtv/hwui-port \
  --androidfw-sources /home/tv/.cache/archtv/androidfw-port \
  --framework dist/apk/aosp-animation-rendernode-1 \
  --art /home/tv/.cache/archtv/art-host/host/art-13.0.0 \
  --tools /home/tv/.cache/archtv/apk-build-tools \
  --output dist/apk/critical-host-check
```

Pasa en ART con -Xint -Xcheck:jni: 2298 llamadas cubren enteros de 32/64 bits,
booleanos, argumentos y retornos float/double/int/long, retorno void, cero
argumentos y una firma con doce
argumentos mixtos que utiliza registros y pila. Se incluyen extremos enteros,
valores negativos, NaN e infinito. Los cuerpos host de prueba comprueban que
reciben los dos contextos nulos. Una prueba de compilación negativa rechaza un
argumento jobject. `reports/aosp-critical-host/` conserva comandos, diagnósticos,
hashes, resultados y el error de compilación esperado.

## Integración pendiente

Esta prueba verifica el adaptador con funciones de prueba. Todavía no envuelve
ni ejecuta el JNI original RenderNode, y no acredita dibujo, animación o
compatibilidad general de llamadas nativas APK. La integración deberá comprobar
las firmas y anotaciones de cada método original antes de registrar su entrada
adaptada. Skia y el enlace HWUI siguen pendientes por separado.
