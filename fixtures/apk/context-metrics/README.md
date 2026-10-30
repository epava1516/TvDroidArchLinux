# APK de métricas y callbacks

Segunda aplicación propia, compilada exclusivamente contra el SDK público API 28.
No importa clases del anfitrión. Comprueba que getApplicationContext devuelve un
Application, que Activity y Application comparten Resources, y que getString lee
el nombre de esta APK. Registra ComponentCallbacks2 en Application.

Cada cambio de configuración comprueba primero las dimensiones dp y orientación
contra Resources, y actualiza el TextView con dimensiones y número de callbacks.
La creación y los callbacks deben ejecutarse en el Looper principal. Al destruir
la Activity se elimina el listener.

```sh
python tools/apk/build_fixture.py --fixture context-metrics \
  --tools /home/tv/.cache/archtv/apk-build-tools --output dist/apk/metrics-new
python tools/apk/verify_metrics_apk.py \
  --art /home/tv/.cache/archtv/art-host/host/art-13.0.0 \
  --runtime-dex dist/apk/apk-context-application-1/dex/classes.dex \
  --linux-library /home/tv/.cache/archtv/smithay/target/debug/libarchtv_aosp_linux.so \
  --resources-library dist/apk/androidfw-clang-1/libarchtv_resources_linux.so \
  --output dist/apk/metrics-check-new
```

Los destinos deben ser nuevos. El builder conserva counter como opción por
defecto y usa el toolchain común fijado en ../counter/toolchain.json. La clave de
firma de laboratorio permanece en la caché, fuera de Git. golden/metadata.json
fija el SHA-256 de la APK y los hashes de fuentes/herramientas. Una nueva firma
puede cambiar el APK: no se afirma reproducibilidad binaria.

Evidencias en reports/aosp-context-metrics/: ejecución ART con 1280×720 →
1920×1080 → 1080×1920, y resize Wayland real 960×540 → 800×450. El verificador
Wayland admite --apk, --activity, --text-before y --text-after; su result.json
conserva la invocación exacta y hashes. Se ejecutó en una unidad systemd temporal
con KillMode=control-group para garantizar limpieza de procesos.

Se usan Context, Resources y Application originales portados; Activity y TextView
siguen siendo el subconjunto propio. No prueba APK arbitrarias, Application
personalizada, recreación de Activity, HiDPI, audio, servicios ni aislamiento.
