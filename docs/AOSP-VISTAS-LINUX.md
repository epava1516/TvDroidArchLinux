# Inicio del port de vistas originales

El modo experimental --with-views de build_aosp_queue.py incorpora View,
ViewGroup y ContextThemeWrapper originales, sin modificar, además del conjunto
Context/Resources/Looper existente. Compilan contra la referencia interna fijada;
la referencia completa no entra en el JAR ni en el DEX de ejecución. Las tres
fuentes ya estaban fijadas en framework-study.json. Se conserva la excepción
previa de cuatro bindings sysprop generados, documentados por separado.

```sh
python tools/apk/build_aosp_queue.py --with-views \
  --sources /home/tv/.cache/archtv/aosp-framework-study/pinned \
  --reference /home/tv/.cache/archtv/aosp-compile-tools/android-all-13.jar \
  --tools /home/tv/.cache/archtv/apk-build-tools --output dist/apk/views-new
python tools/apk/diagnose_views.py --aosp-build dist/apk/views-new \
  --art /home/tv/.cache/archtv/art-host/host/art-13.0.0 \
  --linux-library /home/tv/.cache/archtv/smithay/target/debug/libarchtv_aosp_linux.so \
  --resources-library dist/apk/androidfw-clang-1/libarchtv_resources_linux.so \
  --output dist/apk/views-diagnostic-new
```

Los destinos deben ser nuevos. Este conjunto no sustituye el runtime de las APK:
contiene View/ViewGroup originales que entran en conflicto con las clases propias
del prototipo. No debe combinarse con el DEX anterior para afirmar un port.

## Primer diagnóstico conservado

reports/aosp-views-linkage/ conserva procedencia, compilación e intento de carga
real en ART. ContextThemeWrapper se inicializa y resuelve sus tres constructores
públicos. View y ViewGroup no se cargan: ART devuelve ClassNotFoundException aun
estando sus definiciones presentes en el DEX. El diagnóstico registra
all_three_classes_linked=false. Un diagnóstico terminado no es una prueba de
interfaz funcional; todavía no se construye ningún objeto View.

El inventario externo enumera referencias android.* y com.android.* ausentes de
este DEX completo. Es estático: incluye rutas no ejecutadas y no es un cierre de
carga ni una lista de servicios obligatorios. Las cabeceras compiladas muestran
estas interfaces directas ausentes en aquel primer conjunto:

| Clase | Interfaces originales pendientes |
| --- | --- |
| View | Drawable.Callback, KeyEvent.Callback, AccessibilityEventSource |
| ViewGroup | ViewParent, ViewManager |

Estas ausencias son obstáculos de enlace que hay que resolver; la excepción de
ART no identifica por sí sola cuál se encontró primero. Después siguen las
inicializaciones estáticas y el constructor: ViewConfiguration, RenderNode y el
puente de animación, ApplicationInfo y recursos internos de compatibilidad.
La lectura del constructor original confirma esas llamadas; todavía no se ha
alcanzado su ejecución en esta prueba. RenderNode exige estudiar HWUI/Skia y sus
JNI; una ventana JSON del prototipo no cubre esa dependencia.

## Siguiente puerta

Ampliar las fuentes originales y comprobar carga/inicialización sin la referencia
completa. Después, construir una View con contexto y recursos reales, resolver
la frontera gráfica y verificar measure/layout/draw y entrada. Mantener el
contador y la APK de métricas como regresión, hasta poder retirar sus View,
ViewGroup, TextView y Activity propios. Dibujado, ViewRootImpl, Window, widgets,
accesibilidad e integración de APK siguen abiertos.


## Inicialización original y estados de View

El conjunto posterior añade las fuentes originales de Drawable, KeyEvent,
AccessibilityEventSource, ViewParent, ViewManager, StateSet, Property,
FloatProperty, Color y ActionMode. No se modifican ni se extraen sus interfaces
como sustitutos parciales: se compilan las clases originales completas.

StateSet necesita R.styleable.ViewDrawableStates. view_resource_bindings.py genera
únicamente ese binding desde attrs.xml y public-final.xml originales de la misma
revisión, ambos con tamaño y SHA-256 fijados. Los diez IDs se ordenan por ID de
recurso. ResourceBindingCheck compara el array generado con el de la referencia
Android verificada, en classloaders JVM separados durante el build. La comparación
es obligatoria; no se copia R ni otro bytecode de esa referencia al runtime.

Este binding no es framework-res.apk ni proporciona estilos/temas o las otras
tablas R.styleable. Las solicitudes a campos ausentes seguirán fallando. El JAR
framework incluye el binding generado; el comprobador JVM queda fuera de él y
del DEX.

El diagnóstico ART comprueba las 1.024 combinaciones de StateSet, el orden de
IDs, coincidencias positivas/negativas y el rechazo de la máscara 1024. Prueba
también las funciones estáticas originales MeasureSpec, resolveSize,
resolveSizeAndState y getDefaultSize, antes de construir un contexto de vistas.
Esto verifica algoritmos originales; todavía no acredita measure/layout de un
objeto View, su dibujo ni la compatibilidad según targetSdk de una aplicación.

Las evidencias posteriores se guardan en reports/aosp-views-initialization/.
La ejecución previa sin binding se conserva allí como frontera de diagnóstico;
el resultado final y sus logs distinguen inicialización y resolución de firmas.

El resultado final carga e inicializa las tres clases: View (cuatro constructores
públicos), ViewGroup (cuatro) y ContextThemeWrapper (tres). Pasan StateSet y los
helpers de tamaño. El conjunto conserva 67 fuentes Java originales, los cuatro
bindings sysprop previos y el nuevo binding R generado desde XML. Sigue pendiente
invocar un constructor de View con contexto real y resolver ViewConfiguration,
RenderNode/JNI y recursos de sistema. No se ha retirado la interfaz propia del
runtime de las APK.
