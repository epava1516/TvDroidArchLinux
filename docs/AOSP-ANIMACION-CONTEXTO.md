# Política de animación original y contexto visual

El conjunto experimental compila 97 fuentes Java originales sin modificarlas,
con los cuatro bindings sysprop precompilados ya documentados y el binding de
estados generado desde XML. Añade ValueAnimator, Animator, AnimationHandler,
TimeInterpolator, cuatro clases de interpolación, tres contratos/fábrica de
interpoladores nativos, AndroidRuntimeException, ViewAnimationHostBridge y
RenderNode. La referencia completa sólo se utiliza al compilar.

## Política aplicada desde el host real

WindowManagerGlobal original obtiene el servicio window precargado y aplica
getCurrentAnimatorScale a ValueAnimator.setDurationScale original. La prueba
Wayland publica la política 0.5 desde el anfitrión Rust y comprueba
ValueAnimator.getDurationScale antes de cambiarla manualmente. Su valor inicial
1 no satisface esa comprobación: se verifica la ruta original del servicio.

AnimationPolicyChecks registra un DurationScaleChangeListener original, rechaza
el duplicado y verifica tres cambios: 0.25 → 0 → 0.5, incluidos los estados de
areAnimatorsEnabled. Elimina el listener y comprueba que las llamadas posteriores
no lo notifican. Comprueba también las funciones Java originales de
LinearInterpolator y AccelerateDecelerateInterpolator en puntos concretos.

Esto prueba política, callbacks e interpolación Java. No ejecuta ValueAnimator.start,
un reloj de frames, avance temporal, cancelación, invalidación visual ni los JNI
de NativeInterpolatorFactory. AnimationHandler compila, pero su funcionamiento
completo todavía requiere otras dependencias.

## Identidad de display explícita

LinuxContext implementa ahora siete de los 132 hooks abstractos; los otros 125
siguen fallando expresamente. getDisplayId devuelve únicamente el ID virtual
asociado al bootstrap de AppEnvironment. Las llamadas existentes sin display
mantienen null y lanzan UnsupportedOperationException al solicitar ese ID.
La sobrecarga con ID rechaza valores distintos de 0 antes de abrir recursos.

El probe resuelve el servicio vivo, consulta sus dimensiones y enlaza explícitamente
el display virtual 0 con el contexto. Application/ContextWrapper originales
delegan en ese hook Linux. Esto aporta una identidad para el display de la ventana;
no implementa objetos Display, DisplayManager, métricas físicas ni multidisplay.
La asociación todavía pertenece al bootstrap experimental separado del runtime APK.

El ContextProbe independiente comprueba rechazo del ID 1 antes de inicializar,
ausencia de un display inventado en modo headless y las regresiones anteriores de
contexto, recursos, preferencias y callbacks. También pasa la regresión completa
headless del contador con los adaptadores nuevos.

## Frontera gráfica alcanzada

En la prueba Wayland, el constructor original de View supera ValueAnimator y
ViewConfiguration con el servicio de ventanas y los recursos originales. Ejecuta
RenderNode.create y su constructor original hasta RenderNode.nCreate(String).
ART lanza UnsatisfiedLinkError porque ese JNI gráfico aún no está portado.

No se crea una View funcional ni se acredita dibujo original. Se mantiene el
fallo nativo en el informe; no se sustituye RenderNode por un objeto reducido.
Los próximos trabajos son el enlace gráfico nativo y las dependencias posteriores
del constructor, antes de retirar Activity/View propios del runtime del contador.
El contexto completo, metadatos de paquete, temas, permisos y servicios siguen
incompletos.

## Reproducción y evidencias

Se mantienen los comandos de AOSP-VENTANAS-WAYLAND.md, construyendo el conjunto
actual --with-views y un nuevo probe. Para el ensayo registrado se usaron:

- framework: dist/apk/aosp-animation-rendernode-1;
- probe del servicio: dist/apk/window-animation-rendernode-service-1;
- runtime de regresión: dist/apk/apk-display-context-1;
- bindings: dist/apk/window-aidl-3;
- JNI de recursos: dist/apk/androidfw-system-assets-2;
- perfil de recursos: dist/apk/system-resources-3.

Los destinos de los comandos deben ser nuevos. El verificador Wayland exige el
marcador AOSP_ANIMATION_POLICY_OK y registra por separado view_constructed y las
trazas del fallo. Conserva resize 960×540 → 800×450, tamaño inicial, consultas del
servicio y detección de muerte del proveedor. La APK visible sigue usando la
interfaz del prototipo; el constructor original se prueba en otro proceso ART.

reports/aosp-animation-context/ conserva los logs, snapshots, hashes, procedencia,
regresiones y frames. No cierra A3/A4/A5 ni las puertas generales de rendimiento,
estabilidad, instalación o distribución.

La comprobación posterior de AOSP-INTERPOLADORES-NATIVOS.md ya ejecuta las once
factorías JNI y los objetos C++ originales de interpolación en ART. Es un avance
separado de este servicio Wayland: no añade todavía reloj de frames, ejecución
RenderNode ni animaciones dibujadas.
