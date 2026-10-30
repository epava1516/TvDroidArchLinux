# Estudio de Smithay y Anvil

Revisión documental y de código: 29 de octubre de 2026. El objetivo es un
compositor propio específico de TV, no un tema sobre un escritorio existente.
El estudio inicial no instaló Rust ni compiló Anvil. La ejecución posterior se
registra por separado en [el laboratorio H1](../lab/anvil/README.md).

## Revisión de referencia

Upstream: [Smithay/smithay](https://github.com/Smithay/smithay).
Commit identificado:
[`f581531d479cf2e3307bafb913c5d2bb12860bb3`](https://github.com/Smithay/smithay/commit/f581531d479cf2e3307bafb913c5d2bb12860bb3).

El manifiesto de esta revisión declara Smithay 0.7.0, edición Rust 2024 y Rust
mínimo 1.87. Fijar revisión y Cargo.lock al empezar el prototipo; no confundir
el master revisado con una garantía sobre versiones publicadas.
[Manifiesto](https://github.com/Smithay/smithay/blob/f581531d479cf2e3307bafb913c5d2bb12860bb3/Cargo.toml).

Upstream presenta Anvil como banco de pruebas y Smallvil como recurso de
aprendizaje y punto de partida mínimo. El estudio de Anvil debe guiar decisiones;
no implica adoptar todas sus funciones ni copiarlo como producto terminado.
[Guía de inicio](https://github.com/Smithay/smithay/blob/f581531d479cf2e3307bafb913c5d2bb12860bb3/GETTING_STARTED.md).

## Mapa de lectura

| Archivo en Anvil | Qué estudiar |
| --- | --- |
| src/main.rs | Selección de backend y arranque. |
| src/state.rs | Estados de protocolos, asiento y activación. |
| src/input_handler.rs | Reparto de entrada, foco, capas y pantalla completa. |
| src/winit.rs | Ejecución anidada, GLES, buffers y seguimiento de daños. |
| src/udev.rs | libseat, libinput, dispositivos DRM/GBM y presentación directa. |
| Cargo.toml | Funciones opcionales y dependencias. |

[Directorio de Anvil](https://github.com/Smithay/smithay/tree/f581531d479cf2e3307bafb913c5d2bb12860bb3/anvil),
[Smallvil](https://github.com/Smithay/smithay/tree/f581531d479cf2e3307bafb913c5d2bb12860bb3/smallvil).

## Riesgo gráfico que debe resolverse primero

Anvil documenta backends winit, X11 y TTY/udev. La ruta winit utiliza GLES. La
ruta udev revisada gestiona renderizadores GBM/GLES y descarta un dispositivo EGL
identificado como software al inicializar nodos. Habilitar renderer_pixman en
Cargo no implementa por sí solo un compositor DRM con presentación CPU.
[README](https://github.com/Smithay/smithay/blob/f581531d479cf2e3307bafb913c5d2bb12860bb3/anvil/README.md),
[código udev](https://github.com/Smithay/smithay/blob/f581531d479cf2e3307bafb913c5d2bb12860bb3/anvil/src/udev.rs).

La VM no tiene aceleración 3D validada. La primera prueba debe identificar EGL,
renderizador, formatos y ruta de presentación. Para probar anidado se necesita
un host Wayland de laboratorio, por ejemplo Weston temporal, o otra máquina.
Ese host no será una dependencia del producto. Si se quiere soportar esta VM
sin 3D, habrá que probar buffers de CPU y su presentación directa, además del dibujo.

## Qué no resuelve Smithay automáticamente

La biblioteca no proporciona una interfaz Fire TV, catálogos, políticas de foco
para televisión ni un sistema Android. Waydroid continúa necesitando Binder,
contenedor e imágenes compatibles. La validación gráfica no sustituye pruebas
de arranque completo Android, entrada, audio, vídeo y retorno al shell.

La arquitectura propuesta separa compositor, shell y modelo; consultar
[ARQUITECTURA.md](ARQUITECTURA.md) y los hitos de [ROADMAP.md](../ROADMAP.md).
