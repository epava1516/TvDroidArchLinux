# Shell Rust: prototipo de dibujo

H5 está en curso. Este prototipo mide la biblioteca de dibujo antes de conectarla
al cliente Wayland. No implementa todavía un launcher interactivo. Los elementos
de las capturas son una escena de laboratorio, sin acciones ni catálogo remoto.

## Decisión provisional

- Smithay Client Toolkit y SHM para la futura conexión Wayland del shell.
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

## Composición provisional

La referencia elegida sigue siendo [Fire TV 2026](REFERENCIAS-FIRE-TV.md): navegación
superior, destacado amplio, fila de tarjetas y fila compacta de aplicaciones.
El prototipo utiliza identidad Arch TV, texto local y arte vectorial original.
No incorpora carteles comerciales ni presenta servicios de contenidos como disponibles.

La navegación ocupa la franja superior. El destacado ocupa aproximadamente el
primer 57% de altura; las tarjetas empiezan en y=620 y las apps en y=898, sobre
1080 píxeles. Son medidas del prototipo, no medidas publicadas por Amazon.
Hace falta comparar con la captura principal normalizada y con estados de foco;
no se ha demostrado aún una semejanza precisa con Fire TV.

## Siguientes entregables H5

Cliente Wayland interactivo, modelo de navegación espacial, catálogo real de
archivos desktop, lanzamiento estructurado y carga de iconos en worker. Después,
favoritos/recientes persistentes, búsqueda, teclado en pantalla, menú contextual,
ajustes operativos y validación completa por mando y resoluciones.

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
