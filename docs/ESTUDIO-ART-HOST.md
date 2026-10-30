# ART host para la capa APK

El primer motor que se evalúa es ART compilado para Linux anfitrión. Se busca
ejecutar DEX con sus clases básicas sin arrancar Zygote, system_server,
SurfaceFlinger ni una imagen Android. El compositor y la integración gráfica
siguen siendo propios, en Rust/Smithay.

## Fuentes y alcance

- [Runtime ART en AOSP](https://source.android.com/docs/core/runtime).
- [Formato e instrucciones DEX](https://source.android.com/docs/core/runtime/dalvik-bytecode).
- [Versiones host utilizadas por R8](https://r8.googlesource.com/r8/+/7966a31aa18051a062b33c8cdcc15c09e6a993a2/tools/linux/README.art-versions).
- [Recogida de componentes host por R8](https://r8.googlesource.com/r8/+/7966a31aa18051a062b33c8cdcc15c09e6a993a2/scripts/update-host-art.sh).
- [Lanzador ART de Android 13](https://android.googlesource.com/platform/art/+/android-13.0.0_r3/tools/art).

La exportación host de platform/prebuilts/module_sdk/art consultada incluye
herramientas como dex2oat y dexdump; su directorio bin no incluye dalvikvm.
El conjunto de pruebas de R8 sí recoge dalvikvm, bibliotecas y clases básicas.
La variante elegida para el primer experimento corresponde a android-13.0.0_r3;
su procedencia y hash oficial están en reports/a1-art-host/source.json.

El archivo de R8 incluye componentes adicionales para sus propias pruebas,
versiones de 32 bits, símbolos y framework de producto. Descargar ese archivo
para investigar no convierte todo su contenido en dependencias de nuestra capa.
Habrá que medir y documentar qué componentes se cargan realmente, construir una
selección reproducible y revisar licencias antes de distribuir el runtime.

## Pruebas separadas

fixtures/art-host/RuntimeProbe.java se compila a DEX con las herramientas fijadas
de la fixture APK. Comprueba aritmética, desbordamiento entero, recursión,
interfaces, arrays, excepciones y reflexión. Es una prueba del motor, no una
prueba de compatibilidad Android. Se construye con:

```bash
python tools/apk/build_art_probe.py --tools "$HOME/.cache/archtv/apk-build-tools" --output dist/apk/art-probe-nueva
```

La segunda prueba coloca la APK original del contador en el classpath y solicita
su MainActivity mediante reflexión. No se incluyen sus fuentes Java ni clases
recompiladas de la app en el proceso host. Sin una implementación de android.app.Activity
y sus dependencias, la carga debe fallar explícitamente. Ese fallo identifica
una frontera real; no se acepta como ejecución funcional de la APK.

Una vez resuelta esa frontera, la puerta sigue siendo ejecutar el ciclo de vida
y el código de la APK, cargar sus recursos, recibir entrada y guardar estado.
Ni imprimir un contador desde el lanzador ni proporcionar stubs que devuelvan
éxito sin comportamiento permite cerrar A1/A2.

## Resultado del primer experimento

El DEX semántico termina con código 0 y DEX_SEMANTICS_OK total=9. Se ejecutó
con ART host de 64 bits y -Xint, sin compilación de la aplicación. La carga de
la APK original termina con código 1; -verbose:class revela que MainActivity
se encontró y falló al resolver Landroid/app/Activity;. La excepción final de
Class.forName, por sí sola, sólo muestra MainActivity y no permite atribuir la causa.

El lanzador intenta abrir framework/core.art, ausente en esa ruta del conjunto,
y continúa en modo sin imagen precompilada. Sus mensajes se conservan completos;
no se presenta el arranque del motor como libre de avisos ni como validación de
su consumo, aislamiento o compatibilidad general. La API 28 usada para compilar
la fixture y ART 13 del laboratorio son componentes distintos.

Para repetir desde una caché nueva:

```bash
python tools/apk/fetch_art_host.py "$HOME/.cache/archtv/art-host"
python tools/apk/run_art_probe.py --runtime "$HOME/.cache/archtv/art-host/host/art-13.0.0" --dex dist/apk/art-probe-nueva/dex/classes.dex --apk fixtures/apk/counter/golden/counter.apk --output dist/apk/art-ejecucion-nueva
```

El extractor rechaza un destino ya existente, verifica tamaño y hashes antes de
extraer y limita rutas/tipos/tamaño de entradas. El código 0 del comprobador
significa que pasó la prueba del motor y se observó la frontera de API esperada.
result.json mantiene apk_functional_pass=false explícitamente. Ese ensayo conserva
su valor como prueba del motor sin API. El ensayo posterior añade runtime/apk y
ejecuta el DEX del contador con recursos y preferencias: ver CONTRATO-APK.md y
reports/a1-counter-headless/. El siguiente paso sigue siendo la ventana Wayland.

## Investigación modular de la plataforma original

La entrada vigente sigue en [ESTADO.md](ESTADO.md); estos comandos reproducen la
extracción estática y el ensayo, no instalan ni arrancan Android. Los outputs
deben ser nuevos y requieren espacio para imagen y payloads. La URL/tamaño y
hashes están fijados en runtime/aosp/platform-image.json; la imagen SDK se mantiene
en caché como input de investigación y conserva NOTICE, sin incorporarse a paquetes.

```sh
python tools/apk/extract_platform_image.py \
  --archive "$HOME/.cache/archtv/aosp-platform-33/x86_64-33_r02.zip" \
  --output "$HOME/.cache/archtv/aosp-platform-33/extraction-new"
python tools/apk/extract_platform_modules.py \
  --image "$HOME/.cache/archtv/aosp-platform-33/extraction-new/system.img" \
  --output "$HOME/.cache/archtv/aosp-platform-33/modules-new"
python tools/apk/read_platform_classpath.py \
  --system "$HOME/.cache/archtv/aosp-platform-33/modules-new/system" \
  --modules "$HOME/.cache/archtv/aosp-platform-33/modules-new/modules" \
  --sdk 33 --output "$HOME/.cache/archtv/aosp-platform-33/classpath-new.json"
python tools/apk/verify_isolated_bootstrap.py \
  --platform-classpath "$HOME/.cache/archtv/aosp-platform-33/classpath-new.json" \
  --platform-resources "$HOME/.cache/archtv/aosp-platform-33/modules-new/system/framework/framework-res.apk" \
  --output dist/apk/isolated-platform-new
```

El extractor usa sfdisk y debugfs en modo lectura, sin loop mounts, y verifica
SHA-256 de la imagen y metadatos LP. Sólo admite el layout fijado de un dispositivo,
extents lineales LP 10.0; falla en otros formatos. El lector protobuf sólo admite
el esquema fijado y límites SDK numéricos, no codenames futuros. El ensayo conserva
core/JNI del host, usa jars no básicos del SDK en classpath de aplicación y no
acredita identidad de boot classloader ni compatibilidad entre builds.

La siguiente adaptación debe preservar handles/ownership del JNI original:
ApkAssets utiliza Guarded<unique_ptr<const ApkAssets>>, mientras que el adaptador
anterior usa tokens de un mapa propio. Enlazar sólo nativeOpenXml original con
esos tokens sería incorrecto. Las cuatro fuentes originales de recursos/XML
están [identificadas y verificadas](../reports/aosp-platform-bootstrap/original-resource-jni-source-study.json);
su integración y ejecución todavía no están demostradas.
