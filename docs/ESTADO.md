# Estado real del proyecto

Actualizado: 30 de octubre de 2026 (Europe/Madrid). Los informes usan UTC.

## Dirección actual

Compositor Wayland propio en Rust/Smithay y shell Rust con referencia Fire TV
2026. **H0–H5 comprobados en VM; H6–H9 pendientes.** Existe un workspace
Cargo con compositor propio, modelo de foco y cliente SCTK. El shell Rust interactivo está implementado y validado en H5. La salida DRM/Pixman ya está comprobada desde TTY. Anvil está compilado y probado como referencia upstream.

## Limpieza realizada

Se ha detenido la sesión de prueba anterior y retirado del sistema el paquete
archtv-shell 0.2.0, labwc, swaybg y sus dependencias exclusivas: 19 paquetes en
la transacción, incluidos wlroots0.20 y libsfdo. Se conservan Mesa, Wayland,
Foot, la base del sistema, audio y Waydroid. Durante H1 se reinstalaron bibliotecas
de entrada, libseat y otras dependencias para el laboratorio Rust; no se reinstaló
el compositor anterior.

El árbol activo ya no contiene la interfaz GTK, tema/configuración, archivos de
sesión, instaladores gráficos, receta ni paquetes generados anteriores. La
configuración personal de esa sesión también se ha retirado. El sistema queda
en consola; no se ha alterado el servicio remoto de desarrollo ni el arranque UEFI.

## Copia previa

Copia fuera del repositorio, verificada antes de retirar archivos:

`/home/tv/archivos/archtv-anterior-20261029-LJ4tOw/`

- repositorio-anterior.tar.gz: fuentes, documentación, inventarios y artefactos anteriores; excluye .git.
- configuracion-usuario.tar.gz: configuración personal anterior.
- SHA256SUMS: hashes comprobados de ambos archivos.

Es una copia histórica, no una dependencia ni un instalador activo. Los registros
anteriores y las referencias visuales de la implementación retirada quedan allí.

## Estado de Android y gráficos

Waydroid, sus imágenes y datos se conservan. La prueba anterior informó sesión y
contenedor RUNNING, pero no confirmó sys.boot_completed=1 y mostró lentitud y
avisos ANR. La integración Android sigue en H6. Tras ampliar la VM a 7,7 GiB, una prueba
nativa confirma sys.boot_completed=1 a los 79 segundos y captura el escritorio
Android sobre DRM/Pixman; reports/h6-boot-probe/.

Esta VM dispone de unos 1,9 GiB de RAM. No tiene aceleración 3D validada, pero H1
demostró renderizado anidado por CPU con Mesa llvmpipe. La presentación DRM/KMS
directa está comprobada en H3; el rendimiento del producto sigue pendiente.

## H1 comprobado

- Rust y Cargo 1.99.1 instalados, junto con las dependencias de laboratorio.
- Revisión Smithay f581531d479cf2e3307bafb913c5d2bb12860bb3, checkout sin cambios.
- Cargo.lock guardado; build de Anvil con winit, sin funciones predeterminadas,
  un trabajo y símbolos de depuración desactivados. Primer build: 11 min 53 s.
- Revalidación con --locked correcta y cliente weston-simple-shm mostrado dentro
  de Anvil; se comprobaron commits y callbacks de frame y se inspeccionó la captura.
- Proceso Anvil durante una muestra de 3 s con cliente animado: PSS 128972 KiB
  (unos 126 MiB), CPU 68,64% de un núcleo. No es una medición de reposo ni del producto.
- Procesos y sockets temporales cerrados al finalizar; no hay sesión nueva en TTY.

El log presenta avisos de extensiones EGL/DMA-BUF y una consulta inicial
BAD_SURFACE de edad del buffer; el cliente siguió presentando frames. La prueba
solo valida SHM y presentación anidada, no DMA-BUF Android ni entrada física.

Ver lab/anvil/README.md, reports/anvil/ y reports/anvil-build-environment.txt.

## Comprobaciones y evidencia

- scripts/check.sh verifica los scripts y manifiestos conservados.
- reports/estado-limpieza.txt registra ausencia de paquetes, procesos y archivos retirados.
- reports/paquetes-instalados.txt y paquetes-explicitos.txt registran el estado actual.
- reports/sistema.txt identifica kernel, memoria y zram.

Los presupuestos de rendimiento de ROADMAP.md son objetivos de ingeniería;
no son mediciones de un desarrollo que todavía no existe.

## H2 comprobado: compositor propio

Workspace Rust implementado con Smithay fijado, núcleo de foco y cliente SCTK.
Compilación, Clippy con avisos como errores y dos pruebas de foco correctos.
La prueba gráfica del 29 de octubre a las 23:05 UTC comprobó diez ciclos de
cliente, fullscreen, foco, cambio real 960×540 → 800×450, frames de
weston-simple-shm y retirada del socket al terminar con SIGTERM.

Se corrigieron el envío de respuestas Wayland durante reposo, el tamaño aplicado
síncronamente por winit y el registro simultáneo de superficies pendientes.
Captura inspeccionada: cliente externo visible dentro del compositor propio.
Evidencia: reports/h2/, reports/h2-build.log, reports/h2-clippy.log y
reports/h2-core-tests.log. Reproducción en DESARROLLO-RUST.md.

Las pruebas posteriores añaden popup, reposicionamiento, captura del teclado y
recuperación de foco al cerrarlo. Teclas efectivas verificadas mediante H3.

## H3 comprobado en VM

DRM/KMS directo, Pixman sobre dos buffers presentables XRGB8888 lineales,
1280×800 a 60 Hz. Cliente SHM propio visible sin Weston ni otro compositor.
Captura del buffer mostrado inspeccionada y estado KMS registrado.

Prueba: scripts/84-drm-smoke.sh, con una sesión PAM/logind temporal en tty2.
Right, Return y ntilde recorren uinput → libinput → mapa español → cliente.
El popup captura el teclado y lo devuelve al padre tras cerrarse. Ctrl+Alt+F1
cambia a tty1; volver a tty2 reactiva entrada y presentación (page flip confirmado).
SIGTERM termina la sesión, retira procesos y devuelve la VT inicial.

Se corrigió la gestión de pausa/reanudación: logind/libseat conserva la propiedad
de DRM master; el compositor no intenta recuperarla por su cuenta. El aviso
inicial de Smithay al intentar adquirir master no impide los modesets concedidos
por logind; el ensayo verifica presentación y reanudación, no solo ese mensaje.

Evidencia en reports/h3/. Esta comprobación no valida mando físico, Android,
GPU real, DMA-BUF de clientes, audio ni presupuesto de rendimiento.

## H4 comprobado en VM

Supervisión del proceso que ocupa el rol de shell mediante --shell -- PROGRAMA.
Identidad por conexión Wayland privada heredada; no se confía en app_id o PID.
Canal privado independiente con HOME, RESUME y QUIT; mensajes y trabajo por
iteración acotados. El fallo inicial o posterior del shell se registra y limita
los intentos, manteniendo el compositor y sus aplicaciones.

Prueba del 29 de octubre a las 23:25 UTC: Inicio recupera el shell, RESUME vuelve
a la app, cerrar la app devuelve al inicio, tres reinicios del shell conservan
una segunda app y el cuarto fallo activa el límite. Ctrl+Alt+Retroceso permite
salir incluso después del límite. Los destructores DRM se ejecutan al terminar;
se corrigió una referencia circular del temporizador de supervisión al event loop.

D-Bus, PipeWire, PipeWire Pulse y WirePlumber activos durante el ensayo. Se ha
utilizado archtv-test-client como cliente de prueba del rol, no una interfaz TV.
Evidencia: reports/h4/, reports/h4-build.log y reports/h4-clippy.log.

## H5: del renderer al shell interactivo

El prototipo aislado tiny-skia/fontdue se conserva en --render-probe para las
mediciones iniciales. El producto ya incluye conexión SCTK/SHM, catálogo real,
persistencia, búsqueda, teclado en pantalla y ajustes. Sus evidencias están
separadas de las medidas del prototipo en reports/h5/.

En las pruebas de entrada se añadió liberación de teclas al pausar la sesión o
retirar un dispositivo, conservando las retenidas por otro teclado. Tras volver
de VT se comprobó texto «a» normal, sin Ctrl/Alt retenidas, además de la
reanudación de presentación. Evidencia en el informe H3 más reciente.

## Desarrollo interactivo y seguimiento

El cliente Wayland del shell, catálogo desktop, navegación, búsqueda/teclado en
pantalla, menús de favoritos/orden/ocultación y persistencia ya están implementados
y compilados. Pasan ocho pruebas unitarias entre núcleo y shell. La prueba
gráfica nativa utiliza uinput; el mando físico pertenece a H7.

Graphify 0.9.97 instalado con mapa local AST/Cargo, consultas y vistas interactivas.
El roadmap sigue siendo la fuente del estado de cada hito. Ver GRAPHIFY.md.

## H5: flujo interactivo comprobado a 1080p

Prueba nativa del 30 de octubre a las 00:31 UTC: todos los recorridos de la
interfaz pasan con teclado uinput. Foot recibe texto real, vuelve a primer plano
y se cierra; Inicio restaura el shell. Volumen/silencio PipeWire y radio Wi-Fi
cambian y recuperan sus valores originales. Se confirma persistencia después de
reiniciar el shell y un nuevo frame visible. IPv4 e IPv6 están denegados en la
sesión; no se inicia Android. Evidencia completa en reports/h5-interactive/.

Se añadió selección de modos DRM anunciados por el conector. Menú reconoce
XF86MenuKB además de Menu/F10. La pulsación larga usa también las marcas de
tiempo del evento para conservar su comportamiento si se retrasa un frame.
La comparación visual ahora mide cinco elementos contra la fotografía normalizada
Fire TV 2026; ver COMPARACION-FIRE-TV.md. El shell incluye cabecera de iconos y
un fondo original cargado en worker. La presentación anidada real pasa a 720p,
1080p y 4K con coincidencia de dimensiones, contenido y orientación. Evidencia
en reports/h5-resolutions/. Esta VM no anuncia DRM 4K: no se afirma soporte
nativo 4K ni rendimiento de producción.

El recorrido completo de interacción también pasa a 1280×720 sobre DRM nativo
(01:12 UTC), incluida persistencia y restauración de controles. H5 queda
comprobado en esta VM; los mandos físicos y los presupuestos de rendimiento
permanecen en H7. H6 sigue pendiente de arranque Android completo y aplicación.

## H6: arranque y aplicación en validación

La VM dispone ahora de 7,7 GiB de RAM y cuatro vCPU. La primera prueba tras
la ampliación confirma arranque completo y escritorio Android, sin crash en
el registro capturado. La sesión combinada permite iniciar Android desde
ajustes y abrir el VLC oficial x86_64 desde el buscador del shell, así como
volver con Inicio y reanudar. Hubo un aviso ANR de System UI durante el inicio
de VLC; la estabilidad sigue pendiente. Las pruebas multimedia y de recuperación
se documentan por separado; H6 continúa abierto.

La dirección futura AOSP propia está registrada en AOSP-NATIVO.md, con etapas
posteriores al roadmap actual y criterios explícitos para sustituir Waydroid.

Primer ensayo multimedia: el tutorial de VLC pausó la reproducción. Tras cerrarlo
se decodificaron frames iniciales del clip original, pero las capturas posteriores
quedaron idénticas y el monitor de audio no mostró señal continua. Esto no acredita
audio/vídeo funcional; se conserva como resultado incompleto en h6-integration/.

## Incidente de VM durante las pruebas multimedia

El usuario confirmó un cuelgue de toda la VM y la reinició. Se conservaron los
logs de kernel con TSC inestable, cambio a kvm-clock y stall RCU. La causa aún
no está demostrada: [INCIDENTE-VM-20261030.md](INCIDENTE-VM-20261030.md).
El ensayo VLC TV/software sí muestra avance del vídeo; el audio continuo sigue
sin validarse. El control con el reproductor AOSP detecta audio pero mantiene
el vídeo congelado. Ninguno cierra H6. Tras el reinicio Android queda detenido
mientras se revisa la estabilidad de la VM.
