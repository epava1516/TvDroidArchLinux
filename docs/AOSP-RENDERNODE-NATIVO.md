# Port gráfico original: frontera RenderNode

## Evidencia y decisión

La prueba ART/Wayland registrada en `reports/aosp-animation-context/wayland/`
alcanza `RenderNode.nCreate(String)` y falla por JNI ausente. Todavía no hay
construcción ni dibujo de una View original.

Se inspeccionaron cuatro archivos originales de frameworks/base en la misma
revisión bff944d05cd47d2b3b713565d3f00d512840d282 usada por el framework Java.
`reports/aosp-rendernode-study/sources.json` conserva URLs, tamaños y SHA-256;
los extractos numerados conservan las decisiones de construcción y ownership.
Esta muestra no representa el cierre completo de dependencias.

El JNI original crea un `android::uirenderer::RenderNode`, incrementa su
referencia fuerte y devuelve su dirección. El finalizador devuelve una función
que decrementa esa referencia. No basta con devolver un identificador o reservar
memoria: el destructor también participa en la eliminación de display lists.
El constructor incorpora AnimatorManager y propiedades gráficas originales.

La receta original `libs/hwui/Android.bp` declara `libhwui` con
`host_supported: true`. Incluye RenderNode.cpp y el JNI de RenderNode entre los
archivos comunes. Por ello la siguiente ruta de construcción será estudiar y
reutilizar esa variante host, antes de sustituir internals gráficos por código
propio. La declaración host no prueba que ya compile en nuestra distribución.

## Dependencias identificadas

- `libskia` se incorpora mediante `whole_static_libs`.
- Los defaults comunes declaran libbase, HarfBuzz, Minikin y libui-types; la
  variante host añade libandroidfw y libutils estáticas.
- El conjunto JNI también requiere libcutils, liblog, zlib, JPEG,
  libnativehelper_lazy y libziparchive_for_incfs.
- RenderNode.h enlaza propiedades, matrices, AnimatorManager, display lists y
  tipos Skia; RenderNode.cpp incluye además interfaces del renderthread.

El proyecto ya ha compilado androidfw y parte de sus dependencias para ART host.
Antes de reutilizar sus archivos hay que comprobar revisiones, ABI C++, opciones
y símbolos contra la receta gráfica. No se presupone compatibilidad por nombre.

La variante host omite varias implementaciones exclusivas Android, entre ellas
CanvasContext.cpp, RenderThread.cpp y las pipelines GPU. Por tanto conseguir un
objeto RenderNode host tampoco prueba presentación de ventanas: el recorrido
de grabación y rasterizado debe verificarse por separado y después conectarse
con el productor de superficies Wayland del proyecto.

## Próximas comprobaciones necesarias

1. Fijar el cierre de fuentes y configuración de Skia/Minikin/HarfBuzz y de la
   variante host HWUI, incluyendo sus adaptaciones host originales.
2. Compilar con el mismo ABI C++ de ART y obtener errores concretos de enlace,
   sin exportar funciones que simulen éxito para avanzar el constructor.
3. Probar creación, propiedades y liberación del objeto original con JNI
   comprobado; verificar ownership y la limpieza ante errores.
4. Repetir el constructor View original y resolver su siguiente dependencia.
5. Probar Canvas/display list y comparar píxeles antes de acreditar dibujo;
   después verificar presentación, resize y cierre sobre Wayland real.

No se acredita aún ninguna de estas cinco comprobaciones como superada. La
política de animación Java ya probada tampoco acredita un reloj de frames ni
animaciones renderizadas.

## Construcción de objetos host

`runtime/aosp/hwui-sources.json` fija archivos originales de HWUI, Skia,
Layoutlib, cabeceras ui/gui/Vulkan, libnativehelper, Minikin y HarfBuzz. Son
revisiones correspondientes a android-13.0.0_r3. Incluye árboles completos para
estudio; no implica que todos sus archivos se compilen ni que el cierre de
dependencias del runtime esté completo. Las fuentes permanecen fuera de Git.

El descargador de fuentes nativas admite ahora un manifiesto explícito, conserva
la verificación por archivo y limita descarga/extracción con presupuestos
acotados. El comportamiento predeterminado de androidfw se conserva:

```sh
python tools/apk/fetch_androidfw_sources.py \
  /home/tv/.cache/archtv/hwui-port \
  --manifest runtime/aosp/hwui-sources.json

python tools/apk/probe_hwui_host.py \
  --sources /home/tv/.cache/archtv/hwui-port \
  --androidfw-sources /home/tv/.cache/archtv/androidfw-port \
  --output dist/apk/hwui-object-check
```

La segunda orden compila RenderNode.cpp y su JNI por defecto. `--unit` permite
seleccionar otras unidades originales del manifiesto. Comprueba todos los
archivos fijados antes de compilar, utiliza C++20 y las cabeceras libc++ ya
empleadas por el port de recursos, y registra comandos, hashes de objetos,
diagnósticos y símbolos sin resolver. Necesita Clang y `nm` del anfitrión.
No enlaza ni carga una biblioteca: `linked` y `executed` permanecen en false.

La cabecera JNI tiene que ser la original de libnativehelper: la de OpenJDK no
declara `C_JNIEnv`, requerido por JNIPlatformHelp. Skia usa su configuración
`linux/include/config/SkUserConfig.h`; no se copia ni inventa una configuración.

Otra frontera previa a ejecutar en ART está en graphics_jni_helpers.h: sus
macros CRITICAL_JNI_PARAMS incluyen JNIEnv/jclass en host y los omiten en la
variante Android. El framework Java original contiene métodos CriticalNative.
El futuro enlace debe resolver esa convención de llamada explícitamente antes
de registrar estos métodos; compilar el JNI host no acredita su ABI en ART.

### Resultado de la primera compilación

`reports/aosp-hwui-host-objects/result.json` registra compilación correcta de 14
unidades originales: RenderNode, su JNI, RenderProperties, AnimatorManager,
Matrix, CanvasTransform, DamageAccumulator, Animator, Interpolator,
SkiaInterpolator, AnimationContext, LinearAllocator, SkiaDisplayList y
RenderNodeDrawable. No se modificaron sus fuentes. Se comprobaron los 11 374
archivos del manifiesto gráfico y los archivos del manifiesto androidfw antes
de compilar. Se conservan las advertencias originales del compilador.

Los objetos y sus hashes quedan en `dist/apk/hwui-object-final-1`; los comandos,
diagnósticos y listas `nm` de símbolos sin resolver se conservan en el informe.
Un enlace diagnóstico deliberadamente sin las bibliotecas restantes falla:
incluye símbolos de Skia, libutils, liblog y otras unidades HWUI. Ese fallo no
es una prueba del enlace completo ni una incompatibilidad demostrada de esas
bibliotecas; identifica dependencias que aún hay que construir e incorporar.
No se carga ningún objeto de esta prueba en el runtime APK de producción.

La verificación del descargador también acepta un archivo válido y rechaza un
archivo extraído modificado, un archivo comprimido en caché que excede el
presupuesto y un presupuesto de manifiesto fuera del límite permitido. La
verificación del manifiesto androidfw predeterminado continúa pasando.

La siguiente fase de construcción Skia, sus dependencias y la compatibilidad
con Clang 23 se registran en [AOSP-SKIA-HOST.md](AOSP-SKIA-HOST.md). La prueba
numérica F16C pasa; el enlace y la ejecución de HWUI aún están pendientes.

El adaptador tipado de AOSP-CRITICAL-HOST.md ya supera una prueba ART con ocho
firmas y 2298 llamadas de funciones propias, incluidos argumentos mixtos en
registros/pila y rechazo de referencias a objetos. Su integración en el JNI
RenderNode original sigue pendiente; esa prueba no ejecuta métodos RenderNode.

AOSP-RENDERNODE-JNI.md registra la comprobación de las 88 firmas Java/C++
originales y un perfil generado de 16 entradas, con catorce adaptaciones
CriticalNative. Pasa sintaxis contra las funciones originales, pero todavía no
se enlaza ni ejecuta. La construcción de Skia sigue siendo una dependencia.

La construcción posterior de Skia host CPU ya termina y su ejecutable nativo
supera dibujo/recorte/traslación y lectura exacta de 3072 píxeles. Ver
AOSP-SKIA-HOST.md y reports/aosp-skia-raster/. Esto permite continuar el enlace
HWUI; todavía no ejecuta RenderNode ni Canvas Java en ART.
