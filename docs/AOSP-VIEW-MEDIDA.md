# Medida de View original y siguiente frontera de layout

El perfil original añade LongSparseLongArray, sin modificar la fuente de Android
13 fijada en framework-study.json. View.measure utiliza esta estructura para
almacenar medidas. Compilan 103 fuentes originales en dist/apk/aosp-layout-1.
No se implementa una medida alternativa en Linux ni se modifica View.

La prueba WindowServiceProbe ejecuta cinco casos sobre una View original:

- EXACTLY 320×180.
- AT_MOST 210×110: la View base ocupa el tamaño disponible.
- UNSPECIFIED sin contenido ni mínimo: 0×0.
- UNSPECIFIED después de fijar mínimos 96×54: 96×54.
- EXACTLY 320×180 de nuevo, tras los cambios de restricciones y mínimos.

Las dimensiones se leen mediante getMeasuredWidth/getMeasuredHeight. Se conservan
las comprobaciones previas de constructor, contexto, estado inicial y alpha
nativa. El verificador Wayland registra view_measure_pass y view_layout_pass por
separado; el éxito de resize no implica que el layout haya terminado.

## Layout todavía incompleto

La llamada layout(13,17,333,197) entra en setFrame y llega a la notificación de
accesibilidad; falta AccessibilityManager. Se registra VIEW_LAYOUT_BLOCKED y
view_layout_pass=false. No se acredita layout completo, conexiones de ventanas,
dibujo ni sustitución de las vistas propias del contador.

AccessibilityManager original está descargado y fijado para estudio, pero no se
incluye todavía en el conjunto de ejecución. getInstance consulta permisos
INTERACT_ACROSS_USERS / INTERACT_ACROSS_USERS_FULL e identidad de usuario; su
constructor crea Handler y un cliente IAccessibilityManagerClient, carga recursos
de foco e intenta obtener el servicio accessibility mediante ServiceManager.
Su ruta sin servicio es código original, pero antes deben resolverse los
contratos, identidad y política de permisos Linux de forma explícita. La simple
ausencia del servicio no acredita soporte de accesibilidad.

reports/aosp-view-layout conserva el primer fallo de caché ausente y los
resultados finales, registros, comandos y hashes. El framework Android completo
se mantiene como referencia de compilación; no se incorpora al classpath ART.
La prueba se ejecuta con -Xint y -Xcheck:jni, más los enlaces Linux/androidfw/
RenderNode ya verificados. Resize 960×540→800×450, animación y muerte/cierre del
proveedor se verifican conjuntamente, con la View original aún sin conectar a
una superficie. El contador visible conserva las vistas propias del prototipo.
