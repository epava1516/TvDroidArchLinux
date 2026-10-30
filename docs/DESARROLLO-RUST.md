# Desarrollo del compositor Rust

Workspace de producto, separado del checkout upstream usado en H1:

- `archtv-core`: modelo de foco y pruebas sin servidor gráfico.
- `archtv-compositor`: servidor Wayland Smithay; backends winit y DRM/KMS/Pixman.
- `archtv-test-client`: cliente SCTK con buffers SHM, configure, frames y teclado.
- `archtv-shell`: cliente Wayland interactivo; conserva un modo aislado para medir dibujo.

Smithay está fijado al mismo commit que el laboratorio H1. Las dependencias se
resuelven mediante el Cargo.lock raíz. Las adaptaciones de Smallvil conservan
atribución y licencia en THIRD_PARTY.md y licenses/.

## Construcción y comprobaciones

```bash
./scripts/80-rust-build.sh --apply
cargo test --locked -p archtv-core
cargo clippy --locked --workspace --all-targets -- -D warnings
./scripts/check.sh
./scripts/82-rust-smoke.sh --apply
```

En la VM se puede reutilizar el directorio de artefactos de H1 para ahorrar
espacio y compilación, exportando antes de los comandos:

```bash
export CARGO_TARGET_DIR="$HOME/.cache/archtv/smithay/target"
export CARGO_BUILD_JOBS=1
```

La prueba gráfica crea un Weston temporal headless/Pixman y ejecuta el compositor
propio con Mesa llvmpipe. Guarda logs y captura en reports/h2/. Weston es una
herramienta de laboratorio. Esta prueba no demuestra salida DRM/KMS directa.

Para usarlo dentro de otra sesión Wayland:

```bash
cargo run --locked -p archtv-compositor -- --winit -- target/debug/archtv-test-client 0
```

Si se usa CARGO_TARGET_DIR, sustituir la ruta del cliente por la del binario
compilado. El socket se pasa al proceso hijo mediante WAYLAND_DISPLAY. SIGINT y
SIGTERM detienen el bucle, esperan al hijo y retiran el socket. `--exit-after`
y `--test-resize` permiten pruebas acotadas y cambios reales de ventana anidada.

## Ensayo directo en VM

```bash
./scripts/84-drm-smoke.sh --apply
```

Requiere sudo sin interacción, tty2 libre y ninguna sesión local activa. Crea una
sesión PAM/logind temporal para el usuario actual, activa tty2, ejecuta el cliente
SHM y prueba teclas y cambio de VT con un teclado uinput temporal. El teclado
se destruye al terminar. Se restaura la VT inicial incluso si falla la prueba.
Los resultados quedan en reports/h3/, incluyendo captura PNG y estado KMS.
No habilita autologin ni instala un servicio persistente.

Arranque manual desde una TTY local activa:

```bash
archtv-compositor --drm /dev/dri/card0 -- /ruta/archtv-test-client 0
```

`--capture-after SEGUNDOS RUTA.ppm` captura el buffer DRM presentado; es una
herramienta de prueba. La ruta CPU dibuja mediante Pixman en dos dumb buffers
XRGB8888 lineales exportados como DMA-BUF y presenta mediante page flip.
libseat/logind gestiona los permisos y la pausa/reanudación; libinput la entrada.

## Política y supervisión

```bash
./scripts/85-session-smoke.sh --apply
archtv-compositor --drm /dev/dri/card0 --shell -- /ruta/al/shell
```

El flag --shell supervisa el proceso después de --: hasta tres reinicios en
30 segundos, con espera de un segundo. El compositor conserva las apps si se
agota el límite. Inicio/Home y XF86 HomePage recuperan el shell; Alt+Tab permite
volver a la app anterior. Ctrl+Alt+Retroceso termina la sesión como salida de
emergencia. Ctrl+Alt+F1…F12 cambia de VT en el backend directo.

La identidad se asigna a una conexión Wayland privada, no al título, app_id ni
credenciales PID. ARCHTV_CONTROL_FD entrega al hijo un segundo descriptor Unix;
acepta HOME, RESUME o QUIT terminados en salto de línea. El shell debe marcarlo
CLOEXEC y retirar esa variable al lanzar aplicaciones. No se expone un socket de
control público. Las conexiones públicas nunca adquieren el rol de shell.

## Ensayo del shell interactivo

```bash
./scripts/88-shell-smoke.sh --apply
```

Usa tty2 libre y una configuración/catálogo aislados. Prueba Menú y pulsación
larga, persistencia, búsqueda, Foot real, retorno Inicio/Volver y ajustes de
sonido y radio Wi-Fi, restaurando volumen/silencio/radio al terminar. Requiere
una conexión de desarrollo por cable y una salida PipeWire disponible. La
creación de sockets IP queda denegada durante la sesión. No modifica favoritos
ni recientes personales y no inicia Android.

`--mode WIDTHxHEIGHT` selecciona un modo DRM anunciado por el conector; rechaza
modos no disponibles. En winit establece el tamaño inicial de ventana. El ensayo
H5 elige 1920×1080, disponible en esta VM.

El shell acepta `--capture-states DIRECTORIO` y `--capture-after SEGUNDOS PNG`
para diagnóstico. Esas capturas se codifican durante la prueba y deben omitirse
al medir rendimiento normal.

## Límites actuales

Clientes SHM comprobados en ambos backends. El shell interactivo está en validación; no hay sesión
instalable ni integración Android validada. Popup, grab, reposicionamiento,
límites y mapa español están probados con entrada virtual de kernel. Quedan
pendientes mando físico y plataformas distintas de esta VM.

## Resoluciones del shell real

La prueba 89 requiere el venv de análisis descrito en COMPARACION-FIRE-TV.md:

```bash
CARGO_TARGET_DIR="$HOME/.cache/archtv/smithay/target" ./scripts/89-shell-resolutions.sh --apply
```

Usa Weston headless kiosk como anfitrión de prueba, catálogo aislado de doce
aplicaciones y el compositor/shell reales. Comprueba dimensiones y contenido
cliente frente a la captura presentada a 720p/1080p/4K. No mide rendimiento.
Para el recorrido completo nativo a otro modo anunciado, la prueba 88 acepta
ARCHTV_SHELL_MODE y ARCHTV_SHELL_REPORT; por defecto conserva 1920x1080.
