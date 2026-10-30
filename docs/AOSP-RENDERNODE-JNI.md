# Perfil JNI original de construcción y propiedades RenderNode

El generador `generate_rendernode_jni.py` verifica que RenderNode.java y su tabla
JNI C++ pertenecen a la misma revisión fijada de AOSP. Comprueba los hashes de
ambas fuentes y graphics_jni_helpers.h, y compara nombres, descriptores y
convención CriticalNative de las 88 declaraciones originales. Las 88 coinciden.

Se genera un perfil inicial de 16 entradas en `rendernode-jni.cpp`, con el
contrato completo en `rendernode-jni.json`. Dos entradas conservan JNI normal y
catorce usan el adaptador tipado CriticalHostAdapter sobre las funciones host
originales. La unidad incluye el JNI C++ original; no replica sus operaciones
ni devuelve identificadores ficticios.

El perfil incluye creación/finalizador, clip a límites, identificador único,
posición y tamaño, alpha, descarte de display list y consulta de validez. No
registra animadores ni actualizaciones de posición, cuyo bootstrap de callbacks
requiere trabajo adicional. Tampoco registra las otras entradas originales:
seguirían fallando por JNI ausente si una aplicación las invocase con este
perfil. El objetivo completo del port sigue requiriendo incorporarlas.

```sh
python tools/apk/generate_rendernode_jni.py \
  --sources /home/tv/.cache/archtv/hwui-port \
  --aosp-cache /home/tv/.cache/archtv/aosp-framework-study/pinned \
  --output runtime/aosp/native/rendernode-jni.cpp --check
```

Sin `--check` se regeneran C++ y JSON. La futura construcción debe ejecutar la
comprobación antes de compilar; cualquier cambio manual del adaptador se detecta.

## Evidencia actual

`reports/aosp-rendernode-jni-contract/` registra la comprobación de sintaxis C++
del perfil con las cabeceras y funciones originales. Los catorce adaptadores
CriticalNative compilan con los tipos C++ reales; se conservan las advertencias
originales de HWUI. También se comprueba el rechazo de un archivo generado
obsoleto y de una fuente Java original modificada, antes de escribir el destino.

Esta comprobación no enlaza una biblioteca, no registra las entradas en ART ni
ejecuta un método RenderNode original. La prueba de ocho firmas de
AOSP-CRITICAL-HOST.md es independiente y utiliza funciones de prueba. Después
de terminar Skia habrá que enlazar el cierre nativo HWUI y probar creación,
propiedades y ownership reales en ART antes de repetir el constructor View.
