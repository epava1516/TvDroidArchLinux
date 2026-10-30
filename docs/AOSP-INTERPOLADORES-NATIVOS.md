# Interpoladores originales HWUI ejecutados en ART

La factoría Java `android.graphics.animation.NativeInterpolatorFactory` del
conjunto de 97 fuentes originales ya enlaza sus once métodos JNI. Se compilan
sin cambios los originales HWUI `Interpolator.cpp` y
`jni/android_graphics_animation_NativeInterpolatorFactory.cpp` fijados en
`hwui-sources.json`.

El adaptador `interpolators-jni.cpp` incluye la tabla JNI original y la registra
con `JNIEnv::RegisterNatives` durante JNI_OnLoad. La implementación de cada
constructor y cada interpolación permanece en AOSP. La biblioteca utiliza el
mismo libc++ de ART que el port de recursos; los archivos estáticos de apoyo se
verifican contra su procedencia antes del enlace. No necesita terminar Skia.

## Prueba ejecutada

`verify_native_interpolators.py` compila un programa de prueba separado. Su JAR
no contiene implementaciones `android.*`; ART carga la factoría Java original
desde el DEX del framework. La prueba se ejecuta con `-Xint -Xcheck:jni`:

```sh
python tools/apk/verify_native_interpolators.py \
  --sources /home/tv/.cache/archtv/hwui-port \
  --androidfw-sources /home/tv/.cache/archtv/androidfw-port \
  --androidfw-build dist/apk/androidfw-clang-1 \
  --framework dist/apk/aosp-animation-rendernode-1 \
  --art /home/tv/.cache/archtv/art-host/host/art-13.0.0 \
  --tools /home/tv/.cache/archtv/apk-build-tools \
  --output dist/apk/native-interpolators-check
```

El resultado en `reports/aosp-native-interpolators/` acredita:

- Once factorías originales: accelerate/decelerate, accelerate, anticipate,
  anticipate/overshoot, bounce, cycle, decelerate, linear, overshoot, path y LUT.
- Veinte ciclos de creación/evaluación/delete: 220 objetos C++ originales y
  1100 muestras comparadas con valores esperados de sus curvas.
- Dos objetos adicionales creados desde LinearInterpolator y
  AccelerateDecelerateInterpolator Java originales. Se comparan ambas versiones
  Java y C++ en 1001 posiciones por curva, con tolerancia de 0,0001.
- La LUT vacía conserva el resultado original cero, sin objeto creado. El
  evaluador exclusivo de prueba rechaza el puntero nulo.

El marcador final registra 222 objetos y 3102 muestras. El evaluador y el
destructor de `fixtures/aosp-native-interpolators/native-probe.cpp` son acceso
exclusivo de prueba a punteros válidos creados por la factoría; no forman una
API de producción para APK ni un gestor seguro de identificadores. Las
liberaciones se ejecutan incluso si falla una comparación. Estos ciclos no
acreditan estabilidad prolongada ni ausencia general de fugas.

## Alcance pendiente

Esto no inicia animaciones, no implementa Choreographer, no acredita reloj de
frames ni dibujo de View/RenderNode. Tampoco resuelve la convención
CriticalNative de RenderNode: los once métodos de esta factoría usan JNI normal.
La biblioteca de prueba se carga explícitamente; el runtime APK de producción
todavía no incorpora este bootstrap. Skia, el enlace HWUI restante y la
presentación Wayland continúan por la ruta descrita en AOSP-SKIA-HOST.md.
