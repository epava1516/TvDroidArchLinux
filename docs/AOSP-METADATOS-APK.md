# ApplicationInfo original y metadatos reales de APK

LinuxContext ya implementa getApplicationInfo y getPackageName con datos del
AndroidManifest.xml de la APK actual. Se compila ApplicationInfo.java original,
sin modificar, junto con PackageItemInfo y Parcelling ya portados. El conjunto
de contexto pasa de 54 a 55 fuentes; el conjunto View pasa de 97 a 98.

## Lectura y adaptación Linux

La biblioteca de recursos añade ApkMetadata.nativeRead. OpenArchive/FindEntry/
ExtractToMemory y ResXMLTree/ResStringPool originales de AOSP leen ZIP, XML
binario y cadenas. El adaptador devuelve atributos tipados de manifest,
uses-sdk, application y supports-screens. No interpreta el formato binario con
un parser propio. Las cadenas compiladas se obtienen del valor tipado, no de la
representación raw opcional; JNI conserva UTF-16, incluidos pares sustitutos.

Los límites son 1 MiB de XML descomprimido, 100000 eventos, profundidad 64,
256 atributos por sección, nombres de 256 unidades y salida agregada de
2097152 unidades UTF-16. El límite agregado impide ampliar sin control
una cadena compartida del string pool repitiéndola en muchos atributos.

ApkMetadata construye ApplicationInfo original con paquete, SDK mínimo/objetivo,
UID Linux real del proceso, rutas APK/datos, clase/proceso declarados,
enabled y un conjunto explícito de flags, pantallas, label/icon/theme. Los
defaults numéricos de uses-sdk y de pantallas se contrastaron con PackageParser
de la misma revisión. Con uses-sdk ausente se conservan los campos cero del
ApplicationInfo original usado por ese parser legado. Codenames y referencias
de recursos donde se exige un literal fallan explícitamente.

FLAG_INSTALLED representa la APK registrada en el proceso actual; no acredita
instalación persistente ni una base PackageManager. El flag hardwareAccelerated
refleja la declaración, no acredita GPU. Otros campos conservan los defaults
de ApplicationInfo; no se implementan todas las reglas PackageParser, firmas,
splits, ABI, metadatos Bundle ni descubrimiento de paquetes. Tampoco se cambia
el bootstrap existente de Application para ejecutar una clase personalizada.

El entorno conserva un snapshot y devuelve una copia original ApplicationInfo
por consulta. Modificar la copia no cambia el targetSdkVersion del snapshot.
El SDK de la APK se lee del manifiesto y no se sustituye por el SDK de plataforma.

## Pruebas ejecutadas

`verify_apk_metadata.py` compila una APK propia de recursos con target 27 y la
compara en ART con el contador target 28. Pasa en -Xint -Xcheck:jni:

- Ambas APK devuelven paquete/SDK distintos, UID real, rutas y clase original.
- Se verifican flags literales, proceso privado y label «Aplicación ñ 📺».
- Se rechazan XML corrupto, mínimo SDK 35 en la plataforma 33 y expansión de
  salida por cadenas compartidas. La expansión se genera con AAPT2 original.
- Pasan las regresiones de contexto, contador/persistencia y resize Wayland.

```sh
python tools/apk/verify_apk_metadata.py \
  --runtime-build dist/apk/apk-appinfo-2 --framework dist/apk/aosp-context-appinfo-1 \
  --linux-library /home/tv/.cache/archtv/smithay/target/debug/libarchtv_aosp_linux.so \
  --resources-library dist/apk/androidfw-apk-metadata-4/libarchtv_resources_linux.so \
  --art /home/tv/.cache/archtv/art-host/host/art-13.0.0 \
  --tools /home/tv/.cache/archtv/apk-build-tools --output dist/apk/metadata-check
```

La biblioteca final se enlazó mediante build_androidfw.py --reuse-archives,
conservando los archivos estáticos originales comprobados. Los artefactos de
framework y runtime se deben reconstruir: la clase nueva no está en los DEX
anteriores y nativeRead no está en las bibliotecas de recursos anteriores.

## Constructor View

El perfil de sistema añade config_useDefaultFocusHighlight=true original, con
su ID privado 0x011101e1 verificado por AAPT2: ahora contiene 19 recursos. Con
metadata y este valor, View supera getApplicationInfo y se detiene en la clase
original GradientDrawable todavía ausente. La lectura de metadata y el resize
no acreditan construcción ni dibujo de una View completa.

Artefactos finales: aosp-application-info-1, aosp-context-appinfo-1,
apk-appinfo-2, androidfw-apk-metadata-4, system-resources-appinfo-1 y
window-appinfo-service-2. `reports/aosp-application-info/` conserva las pruebas,
procedencia, logs y frames. Continúan abiertos los pasos gráficos posteriores,
la integración completa del framework y las puertas A3–A5.
