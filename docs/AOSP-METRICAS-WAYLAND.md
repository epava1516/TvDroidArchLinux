# Métricas de Resources y ventana Wayland

El cliente Rust espera el primer xdg_toplevel.configure para arrancar ART. Pasa
su tamaño como -Darchtv.display.width/height y el adaptador construye Resources
original con esas dimensiones antes de crear la Activity. Cuando el compositor
no propone un tamaño, el cliente elige 1280×720 inicialmente y conserva el tamaño
actual en configuraciones posteriores sin dimensiones.

Las nuevas configuraciones se transmiten mediante `configure ANCHO ALTO` al
Handler principal original. Resources.updateConfiguration actualiza métricas,
orientación, dimensiones dp y smallestScreenWidthDp. La densidad existente se
conserva. Esto actualiza recursos; todavía no reproduce recreación de Activity,
onConfigurationChanged ni todo el layout de View Android.

Cada snapshot ready/updated incorpora `display: [ancho, alto]`, leído de
Resources.getDisplayMetrics original. El cliente valida el rango y sólo produce
un nuevo frame cuando esos datos coinciden con el tamaño Wayland actual.
Los tamaños pendientes aún no enviados se condensan al último mientras hay
comandos en vuelo. Se mantiene el límite existente de 16 solicitudes; un cambio
de recursos se envía cuando las anteriores han respondido. No se pierden las
activaciones ya aceptadas por este mecanismo.

## Evidencia

- reports/aosp-display-headless/: 1280×720 → 1920×1080 → 1080×1920 → 1280×720;
  la activación intermedia conserva el contador. Dimensiones cero, fuera del
  presupuesto o no numéricas fallan en el Handler original. Pasan también las
  regresiones anteriores de recursos, persistencia, ráfaga, EOF y errores.
- reports/aosp-display-wayland-resize/: compositor propio anidado en Weston
  headless, cambio Wayland real 960×540 → 800×450 después del primer frame;
  Resources confirma el cambio en main y el cliente produce el nuevo SHM.
- reports/aosp-display-wayland-720/ y reports/aosp-display-wayland-1080/: dos
  sesiones DRM/Pixman por resolución; el primer snapshot ya tiene el tamaño
  correcto. Enter/Espacio y reapertura conservan 0→1→2 / 2→3. Los frames del cliente
  y el scanout coinciden exactamente en RGB en ambas resoluciones.

Para repetir las sesiones, usar las variables habituales de APK-WAYLAND.md y
ARCHTV_APK_MODE=1280x720 o 1920x1080, con ARCHTV_APK_SMOKE_REPORT nuevo para cada
resolución. La verificación toma las dimensiones del resultado y comprueba las
trazas APK_DISPLAY además de los píxeles.

## Pendientes

La prueba anidada verifica WindowHandler.configure después del primer frame.
No acredita cambio físico de modo DRM, hotplug de monitor, rotación física,
HiDPI/escala fraccionaria o adaptación de densidad desde wl_output. Las dimensiones se usan con escala de superficie 1. Se conserva el
presupuesto 1..3840 × 1..2160, no una promesa de modos físicos admitidos.

Recursos de sistema, Activity/View originales, servicios y las puertas de
estabilidad/distribución del roadmap siguen pendientes.

## Sincronización de las capturas

La repetición final a 1080p detectó una captura que coincidía con el frame anterior,
mientras el último page flip estaba pendiente. Se conserva en
reports/aosp-display-capture-race/, junto con las imágenes y la diferencia medida.
El helper también esperaba un número global de frame que podía corresponder a
una vista anterior.

Ahora el helper espera un frame posterior al texto objetivo. `--capture-request`
complementa `--capture-after`: el compositor atiende el archivo de solicitud sin
page flips pendientes y, en este modo, sin cambios de escena pendientes. Publica
el PPM mediante rename y consume la solicitud; admite otra solicitud posterior.
La prueba exige que el scanout coincida exactamente con el frame objetivo, con un
límite de 30 segundos y registro de cada intento, antes de enviar Escape. No es
una medición de latencia. El modo temporizado sin solicitud sigue siendo una
captura única; también espera el ACK de presentación antes de leer el buffer.

La prueba de resize se repite con tools/apk/verify_wayland_resize.py, pasando
--target, --runtime-dex, --linux-library, --resources-library y --output nuevos.
Usa Weston headless/Pixman y el hook --test-resize de winit, con Mesa software;
son dependencias de prueba, no del runtime DRM. Ejecutarla en una unidad temporal
con KillMode=control-group limita la limpieza de todos sus procesos.

Una segunda repetición expuso que el teclado uinput podía enviar eventos antes
de su descubrimiento por libinput. Se conserva en reports/aosp-display-input-readiness/.
El helper ya espera INPUT_ADDED con un nombre de dispositivo único, en lugar
de una espera fija tras crearlo.
