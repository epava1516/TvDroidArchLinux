# RenderNode original ejecutado en ART sobre Linux

El perfil de 16 métodos JNI ya enlaza y ejecuta RenderNode.java y su objeto C++
original de HWUI. La prueba ART crea 64 objetos independientes y verifica IDs,
posición/tamaño, alpha, clip y descarte de una display list vacía. No se ha
grabado ni presentado dibujo de una View original.

## Construcción nativa

`build_rendernode_host.py` toma del Android.bp original las 46 unidades comunes
HWUI y añade HostColorSpace.cpp, la implementación host original. Compila
también las 28 unidades originales de Minikin y el adaptador JNI generado. Se
enlazan las bibliotecas Skia verificadas y las dependencias androidfw ya
construidas, con el mismo libc++ de ART.

El primer enlace identificó las funciones Minikin ausentes y referencias RTTI
que Skia no exporta porque se construye sin RTTI. El perfil HWUI se alineó con
esa opción y se añadió Minikin original; no se añadieron funciones de relleno.
Las interfaces C de tipografía/códecs usan las bibliotecas Linux registradas en
la procedencia. Se instaló harfbuzz-icu 15.0.0-1 y se actualizaron las dependencias
en `manifests/apk-lab.txt`.

`hwui-host-sources.json` fija 15 cabeceras originales adicionales de libui-types
y math. Se omite el enlace de reexportación GraphicTypes.h porque su archivo
real ya está en las cabeceras ui verificadas. Los árboles de dependencias
adicionales no cambian los manifiestos usados para construir Skia.

```sh
python tools/apk/fetch_androidfw_sources.py \
  /home/tv/.cache/archtv/hwui-port --manifest runtime/aosp/hwui-host-sources.json
python tools/apk/build_rendernode_host.py \
  --sources /home/tv/.cache/archtv/hwui-port \
  --androidfw-sources /home/tv/.cache/archtv/androidfw-port \
  --androidfw-build dist/apk/androidfw-clang-1 --skia-build dist/apk/skia-host-6 \
  --aosp-cache /home/tv/.cache/archtv/aosp-framework-study/pinned \
  --art /home/tv/.cache/archtv/art-host/host/art-13.0.0 \
  --output dist/apk/rendernode-host-build
```

El constructor comprueba las fuentes, archivos estáticos y adaptador generado
antes de compilar. Usa un trabajo y conserva comandos, hashes de objetos y logs.
`--resume` se usa tras un fallo terminal: solo reutiliza objetos cuyo comando,
entradas y hash coinciden. Un cambio de opciones recompila lo necesario. El
resultado exitoso actual está en `dist/apk/rendernode-host-1/result.json`.

## Ejecución y límite actual

```sh
python tools/apk/verify_rendernode_art.py \
  --build dist/apk/rendernode-host-1 \
  --linux-library /home/tv/.cache/archtv/smithay/target/debug/libarchtv_aosp_linux.so \
  --framework dist/apk/aosp-animation-rendernode-1 \
  --art /home/tv/.cache/archtv/art-host/host/art-13.0.0 \
  --tools /home/tv/.cache/archtv/apk-build-tools --output dist/apk/rendernode-art-check
```

La prueba usa -Xint -Xcheck:jni y no incluye clases android propias. Invoca las
16 entradas, comprueba idempotencia y propiedades independientes de los 64
objetos, y confirma que setElevation falla por nSetElevation no registrado.
El constructor Java original registra el finalizador original mediante
NativeAllocationRegistry; la ejecución del GC y liberación final no se han
instrumentado, por lo que no se acredita todavía lifecycle completo ni fugas.

El verificador Wayland admite `--window-rendernode-build` junto al perfil de
servicio experimental. Comprueba el hash de la biblioteca y la carga solo en
ese proceso ART. Pasan resize 960×540→800×450, la política de animación Java y
la detección del cierre del proveedor. La APK visible conserva sus widgets de
prototipo; no se usa RenderNode para dibujar esos frames.

El constructor View original ya supera RenderNode y alcanza View.java:5376,
donde requiere Context.getApplicationInfo. LinuxContext todavía rechaza esa API.
El siguiente port debe proporcionar ApplicationInfo original y metadatos reales
de la APK, incluido su targetSdkVersion. No se fija un SDK de aplicación ficticio.

`reports/aosp-rendernode-native/` conserva construcción, prueba ART, servicio,
resultado Wayland y trazas de la siguiente dependencia. El error de enlace
inicial y paquetes instalados están en `reports/aosp-rendernode-host-build/`.
Quedan abiertos las otras 72 entradas JNI, callbacks de posición/animación,
dibujo Java, integración en el runtime APK, GPU y las puertas generales A3–A5.
