# Constructor de View original en Linux

El perfil `--with-views` incorpora GradientDrawable, PorterDuff, BlendMode y
Xfermode originales, sin modificar sus fuentes. Proceden de frameworks/base
Android 13, revisión bff944d05cd47d2b3b713565d3f00d512840d282; sus tamaños y
SHA-256 están fijados en runtime/aosp/framework-study.json. El conjunto compila
102 fuentes originales y empaqueta sus clases internas; la referencia completa
android-all sólo se usa para compilar.

## Dependencias resueltas

View aplica la compatibilidad del target SDK real de la APK mediante
GradientDrawable.sWrapNegativeAngleMeasurements. Inicializar esa clase requiere
inicializar Drawable, que usa PorterDuff.Mode.SRC_IN y BlendMode.SRC_IN.
BlendMode depende a su vez de Xfermode. Se conserva esa inicialización original;
no se omite ni se sustituye por campos propios.

Los informes missing-porterduff y missing-xfermode registran los fallos
intermedios. El perfil final usa dist/apk/aosp-gradient-3 y el servicio compilado
contra ese framework. ART ejecuta con -Xint y -Xcheck:jni, cargando los enlaces
Linux, androidfw y RenderNode ya verificados.

## Alcance

La prueba final construye una View original con Application y Context originales
adaptados a Linux, recursos originales y metadata real de la APK target 28.
Comprueba identidad del contexto, tamaño cero antes de layout, ausencia de padre
e ID, visibilidad inicial, alpha nativa 1 y compatibilidad de ángulos para target
28. También conserva la prueba de proveedor de ventanas: resize 960×540 a
800×450, dimensiones iniciales, política de animación, muerte y cierre.

El contador mostrado sigue utilizando las vistas propias del prototipo. No se
ha presentado ni dibujado esta View original, ni probado measure/layout,
inflación, widgets, Activity original o creación de una instancia de
GradientDrawable. Esta última requiere Paint, Path y sus dependencias gráficas.
El siguiente paso es verificar el ciclo de vistas e integrar el dibujo original
con la superficie Wayland. A3–A5 y las puertas generales siguen abiertos.

Los resultados, comandos, hashes y registros se conservan en
reports/aosp-drawable-bootstrap. Una ejecución exitosa del constructor no
acredita compatibilidad general con APK, consumo ni estabilidad prolongada.
