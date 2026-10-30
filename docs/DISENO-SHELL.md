# Shell Rust: interfaz y mediciones

H5 está comprobado en esta VM. El shell ya es un cliente Wayland interactivo, con catálogo
local de aplicaciones y operaciones reales. Mantiene un modo de dibujo aislado
para comparar bibliotecas y resoluciones. Las primeras capturas de reports/h5/
son una escena de laboratorio; las de reports/h5-interactive/ proceden del
cliente interactivo real con un catálogo de prueba explícito.

## Decisión provisional

- Smithay Client Toolkit y SHM para la conexión Wayland del shell.
- tiny-skia 0.11.4 para formas y rasterizado CPU.
- fontdue 0.9.5 y DejaVu Sans del sistema para texto y caché de glifos.
- Espacio de diseño 1920×1080, escalado a 720p/1080p/4K.
- Caché de glifos por carácter y tamaño; dibujo sin red ni descargas de imágenes.

Esta ruta evita un motor web o un toolkit de escritorio. Debe validarse con
entrada, transferencia SHM y presentación completa antes de decidir su rendimiento.
Fontdue rasteriza glifos; no sustituye un sistema de composición compleja de texto.
Español es el idioma inicial; otros sistemas de escritura requieren evaluación.

## Reproducción

```bash
export CARGO_TARGET_DIR="$HOME/.cache/archtv/smithay/target"
./scripts/86-shell-render-probe.sh --apply
```

Compila el renderer en release. Genera PNG y métricas en reports/h5/. Las muestras
calientes usan diez dibujos de calentamiento y sesenta muestras, y excluyen
la codificación PNG; la medida del proceso sí la incluye.
El máximo RSS del proceso no equivale a PSS en reposo ni al consumo de la sesión.
No son tiempos de entrada a pantalla, ni una demostración de 60 fps.

## Composición medida

La referencia elegida es [Fire TV 2026](REFERENCIAS-FIRE-TV.md). La cabecera usa
ocho iconos compactos; el inicio seleccionado ocupa 66×66 px. Las tarjetas
empiezan en y=608, las apps en y=816 y el panel inferior en y=922, sobre 1080 px.
Las medidas y sus límites están en [COMPARACION-FIRE-TV.md](COMPARACION-FIRE-TV.md).
Los destinos representan funciones existentes: menú, búsqueda, inicio, apps,
recientes, Linux, Android y ajustes.

El fondo cinematográfico original está incluido en assets/hero-home.png; se
decodifica en el worker y se conserva un fondo escalado en caché. Los controles
y los iconos de navegación se dibujan en Rust. El catálogo muestra aplicaciones
locales; los nombres de prueba pertenecen solo al ensayo aislado.

## Validación interactiva

La prueba scripts/88-shell-smoke.sh valida desde DRM/Pixman a 1080p: navegación,
pulsación larga y Menú, favoritos/orden/ocultación, restauración, búsqueda física
y en pantalla, lanzamiento e introducción de texto en Foot, recientes, Inicio,
Volver y cierre. Se modifican y restauran valores reales de PipeWire y radio
Wi-Fi. PNG/SVG se cargan en worker; un PNG dañado usa la alternativa legible.
El catálogo y las preferencias de la prueba están aislados de los personales.

Después de matar el shell se comprueba un nuevo primer frame/foco, la carga de
dos favoritos y un reciente y una nueva captura. El arranque sigue funcionando
con IPv4/IPv6 denegados y sin Android. Las pruebas usan teclado uinput, no un
mando físico. El cotejo visual medido se conserva en reports/h5-layout/. La prueba
89 comprueba buffers y presentación del shell real a distintas resoluciones;
la interacción completa a 1080p se verifica con la prueba 88. Los tiempos de la tabla inferior son del prototipo aislado original,
no del cliente interactivo ni de la presentación completa.

## Primer resultado del renderer optimizado

VM x86_64 VirtualBox, cuatro vCPU, unos 1,9 GiB de RAM; build release con
thin LTO. Sesenta muestras después de diez dibujos de calentamiento:

| Resolución | p50 de dibujo CPU | p95 de dibujo CPU | Buffer RGBA |
| --- | --- | --- | --- |
| 1280×720 | 4,24 ms | 5,33 ms | 3,52 MiB |
| 1920×1080 | 6,93 ms | 8,31 ms | 7,91 MiB |
| 3840×2160 | 23,73 ms | 26,79 ms | 31,64 MiB |

Se alinearon los rectángulos del fondo con píxeles físicos y se retiró su
antialiasing redundante. Antes, el p95 era 22,41 ms a 720p y 61,99 ms a 4K;
la captura conserva bordes redondeados y texto suavizados. Medidas anteriores en
reports/h5/before-pixel-snap.txt y de referencia en pixel-snap-reference.txt. renderer-metrics.txt conserva la
última ejecución, que puede variar por planificación de CPU.

El dibujo a 1080p deja margen dentro de 16,67 ms, pero falta sumar transferencia
SHM, composición, presentación e interacción. El redibujo completo a 4K supera
ese presupuesto. La UI interactiva y las cachés necesitan su propia medición;
no se declara aún una tasa de frames ni consumo de sesión.
