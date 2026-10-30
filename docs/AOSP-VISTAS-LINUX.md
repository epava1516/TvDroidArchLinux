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

## Resultado observado

reports/aosp-views-linkage/ conserva procedencia, compilación e intento de carga
real en ART. ContextThemeWrapper se inicializa y resuelve sus tres constructores
públicos. View y ViewGroup no se cargan: ART devuelve ClassNotFoundException aun
estando sus definiciones presentes en el DEX. El diagnóstico registra
all_three_classes_linked=false. Un diagnóstico terminado no es una prueba de
interfaz funcional; todavía no se construye ningún objeto View.

El inventario externo enumera referencias android.* y com.android.* ausentes de
este DEX completo. Es estático: incluye rutas no ejecutadas y no es un cierre de
carga ni una lista de servicios obligatorios. Las cabeceras compiladas muestran
estas interfaces directas todavía ausentes:

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
