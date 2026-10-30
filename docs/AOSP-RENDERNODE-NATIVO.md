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
