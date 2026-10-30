# Roadmap · Arch TV nativo en Rust

Objetivo: una sesión Linux para televisión con **compositor Wayland propio basado
en Smithay**, **shell en Rust**, apariencia próxima a **Fire TV 2026** y aplicaciones
Linux/Android. La distribución final estará basada en Arch Linux.

Fecha de definición: 29 de octubre de 2026. Se planifica por entregables y pruebas,
sin fechas inventadas. H0–H4 están comprobados en la VM x86_64. El compositor y el cliente de prueba
son propios; H5 conserva pruebas funcionales parciales; H6–H9 siguen abiertos. No hay validación de mando físico. El estudio previo y las fuentes están en
[ESTUDIO-SMITHAY-ANVIL.md](docs/ESTUDIO-SMITHAY-ANVIL.md).

## Alcance inicial

- x86_64 UEFI, un monitor y una aplicación principal a pantalla completa.
- Mando que emule teclado como primera entrada; gamepad/Bluetooth/CEC después.
- Shell con navegación superior y filas, siguiendo la referencia Fire TV elegida.
- Inicio recupera el shell; Volver y flechas llegan al cliente que corresponde.
- Arranque del shell independiente de la disponibilidad de Android o de la red.
- Consumo y tiempos medidos antes de afirmar que el resultado es ligero.

No forman parte de la primera entrega un escritorio flotante general, varios
monitores, HDR/VRR, Xwayland, asistente de voz o catálogos comerciales agregados.
Se podrán añadir mediante decisiones posteriores y pruebas concretas.

## Orden de entrega

| Hito | Resultado | Depende de | Estado |
| --- | --- | --- | --- |
| H0 | Retirar la base gráfica anterior y ordenar el proyecto. | — | Completado |
| H1 | Entorno Rust y ensayo reproducible de Anvil. | H0 | Completado |
| H2 | Compositor propio mínimo y cliente visible. | H1 | Completado en VM |
| H3 | Salida directa TTY y ruta gráfica de la VM validada. | H2 | Completado en VM |
| H4 | Política TV, sesión y recuperación. | H3 | Completado en VM |
| H5 | Shell Rust con diseño Fire TV y uso mediante mando. | H4 | En curso |
| H6 | APK completas sin modificar sobre Linux, sin Waydroid ni boot Android. | H5, A3–A4 | Pendiente; laboratorio Waydroid histórico |
| H7 | Rendimiento, estabilidad y accesibilidad medidos. | H5, H6 | Pendiente |
| H8 | Paquetes propios y sesión instalable. | H7 | Parcial histórico; runtime APK sin empaquetar |
| H9 | Imagen Arch TV e instalación desde cero. | H8 | ISO de laboratorio; instalación/recuperación pendientes |

## Decisión de base APK y dependencias externas

H6 se rige por [el contrato](docs/CONTRATO-APK.md) y las puertas
[D0–D6](docs/ROADMAP-A.md): comparar ART host/glibc, componentes originales
Bionic/AOSP x86_64 y mezclas con fronteras probadas. La primera prioridad es un
experimento vertical con Markor completa, sin boot Android oculto. Los servicios
originales individuales son candidatos, sujetos a cierre y costes verificables.

La aceptación incluye API/servicios externos, ABI Bionic/JNI e ISA por separado.
GMS/microG, proveedores/media y DRM/auth/certificación no se consideran resueltos
por copiar bibliotecas o identificar interfaces. La [matriz](docs/COMPATIBILIDAD-APK.md)
conserva cobertura pendiente y pruebas negativas; se ampliará con APK reales
para esos perfiles. H7 mide también el runtime y servicios, H8 fija licencias y
actualiza componentes coherentes, H9 verifica instalación y recuperación.

## H0 · Limpieza y base documental

Trabajo realizado:

- Copia del repositorio, paquetes generados y configuración personal fuera del
  árbol activo, con hashes verificados.
- Detención de la sesión anterior y retirada de su paquete, compositor, fondo
  y dependencias exclusivas.
- Eliminación de interfaz GTK/Python, configuración de compositor, tema,
  sesiones desktop, receta de paquete, instaladores y pruebas gráficas antiguos.
- Conservación de la investigación Fire TV/Smithay y herramientas de base/Android.

**Aceptación:** no quedan ejecutables ni configuración activa de la sesión
anterior; sus paquetes no están instalados; los scripts conservados pasan sus
comprobaciones; el inventario refleja la máquina limpia. Evidencia en
[ESTADO.md](docs/ESTADO.md) y reports/.

## H1 · Rust y Anvil como laboratorio

Resultado del 29 de octubre: Rust/Cargo 1.99.1 instalados, Anvil compilado con
revisión y Cargo.lock fijados, y cliente SHM visible mediante el backend winit
sobre Weston headless/Pixman. Renderizador de Anvil: Mesa llvmpipe. Evidencia
y reproducción en [el laboratorio H1](lab/anvil/README.md).

1. Instalar y registrar Rust/Cargo y herramientas de enlace según el backend.
   El master estudiado requiere Rust 1.87 como mínimo; comprobarlo en la revisión
   elegida. Candidatos en manifests/build.txt y manifests/platform-candidates.txt.
2. Fijar el commit Smithay de referencia y las dependencias mediante Cargo.lock.
   Guardar versiones del compilador, flags y bibliotecas del sistema.
3. Leer Anvil en este orden: main, state, winit, input_handler y udev. Contrastar
   con Smallvil para separar lo imprescindible de las funciones de laboratorio.
4. Compilar solo los backends y protocolos del ensayo. Limitar trabajos paralelos
   en la VM de 1,9 GiB o usar una máquina de desarrollo con más recursos.
5. Probar Anvil anidado y abrir un cliente Wayland. Como la máquina queda en
   consola, usar otra máquina con sesión Wayland o un host Weston temporal de
   laboratorio; este no será dependencia de ejecución del producto.

**Entregable:** comandos reproducibles y log de compilación/arranque, revisión,
renderizador, formatos, RAM y resultado del cliente.

**Aceptación:** el ensayo arranca y muestra un cliente, o produce una explicación
reproducible de la incompatibilidad gráfica y una ruta de ensayo alternativa.
No pasar al diseño visual completo hasta resolver la viabilidad de presentación.

## H2 · Compositor mínimo propio

Implementados: workspace, modelo de foco probado, servidor SHM/xdg-shell,
fullscreen, seguimiento de daños, cliente SCTK y scripts de construcción/prueba.
Compilación y Clippy sin avisos. Ver [desarrollo Rust](docs/DESARROLLO-RUST.md).
Comprobados: diez ciclos de clientes, fullscreen, resize real, recuperación de foco,
cliente SHM externo, popup visible/reposicionado/cerrado y grab de teclado.
La entrada real del kernel se ensayó en H3 con uinput → libinput → cliente,
incluyendo «ñ» del mapa español. Evidencia en reports/h2/ y reports/h3/.


Crear un workspace Rust con responsabilidades separadas: compositor, shell,
modelo compartido y herramientas de prueba. No crear binarios de relleno para
marcar el hito: cada ejecutable debe tener una función demostrable.

- Bucle de eventos, socket Wayland y vida de clientes.
- Protocolos mínimos para buffers SHM, superficies, salida, asiento y xdg-shell.
- Teclado y mapa español; foco inicial y envío de eventos al cliente.
- Una aplicación a pantalla completa, configure/ack, popups y cierre correctos.
- Renderizado con seguimiento de daños y callbacks de frame.
- Entrada de proceso por argumentos estructurados, sin ejecutar órdenes de shell
  tomadas de datos externos.

**Entregable:** archtv-compositor arranca en el backend de pruebas y muestra un
cliente propio mínimo y una aplicación Wayland existente.

**Aceptación:** abrir/cerrar clientes repetidamente, redimensionar, recuperar el
foco y terminar limpiamente sin dejar socket ni procesos propios huérfanos.
Pruebas de modelo sin GPU y pruebas de protocolo/renderizado en el laboratorio.

## H3 · Salida directa y decisión de renderizado

Resultado: cliente visible desde tty2 sin anfitrión, DRM/KMS con dos buffers
XRGB8888 lineales, Pixman y page flips confirmados a 1280×800/60 Hz en VirtualBox.
Ctrl+Alt+F1, pausa, regreso a tty2, presentación posterior y cierre limpios
comprobados. Captura e información KMS en reports/h3/.

Decisión: soportar la ruta CPU en esta VM. Se importan clientes SHM; DMA-BUF de
clientes Android aún no está anunciado ni validado. No hay copia intermedia del
frame completo: Pixman dibuja sobre el dumb buffer exportado/mapeado como DMA-BUF.
Esto no es una medición de rendimiento ni una declaración de soporte físico.
Entrada virtual de kernel probada; mando físico reservado a H7.


Pasar del backend de laboratorio a una sesión real en TTY:

- logind/libseat, DRM/KMS, conectores, modos y asignación/presentación de buffers.
- libinput, conexión/desconexión de teclado y ratón, cambio y regreso de VT.
- Elegir y probar la ruta EGL/GBM/GLES en hardware compatible.
- Para esta VM sin 3D validado, ensayar una ruta CPU con buffers presentables
  por DRM. Pixman o rasterizar en memoria no bastan sin la presentación completa.
- Registrar formatos/modificadores, tamaño, copias y coste por frame; contemplar
  explícitamente qué se podrá aceptar de los clientes Android.

**Decisión obligatoria:** soportar presentación software en esta VM o fijar GPU
compatible como requisito. Tomarla a partir del ensayo, no de una opción Cargo.
Si no funciona ninguna ruta disponible, resolver este hito antes de avanzar.

**Aceptación:** dibujo y cliente visibles desde TTY sin compositor anfitrión,
entrada física funcional, cambios de VT y cierre que devuelva la consola. Guardar
captura o grabación y logs; repetir en cada plataforma declarada compatible.

## H4 · Comportamiento de televisión y sesión

Comprobado con cliente de prueba ocupando el rol de shell: Inicio global,
RESUME por canal privado, cierre de aplicación → inicio, tres reinicios del
shell sin cerrar la app, límite de fallos y salida de emergencia por teclado.
En el momento de ese ensayo H4, la interfaz de televisión de H5 aún no existía; los resultados posteriores están en H5.

El supervisor entrega conexiones Wayland y de control privadas al hijo. Solo
esa conexión recibe el rol de shell; un cliente público con el mismo app_id no
lo obtiene. El canal acepta HOME, RESUME y QUIT, con lectura no bloqueante y
límite por despacho. No admite órdenes de shell ni lanzamiento arbitrario.
La prueba levanta D-Bus, PipeWire, WirePlumber y retira capacidades heredadas.
Evidencia en reports/h4/ y scripts/85-session-smoke.sh.


- Un cliente principal a pantalla completa; vuelta al shell al cerrar la aplicación.
- Inicio global que recupere el shell desde cualquier aplicación compatible.
- Flechas y Volver enrutados al cliente activo; paneles propios capturan entrada
  únicamente mientras están abiertos.
- Inicio/supervisión del shell con reinicio limitado; su fallo no cierra las apps.
- Canal de control del shell con identidad y operaciones limitadas. La carga de
  imágenes, consultas de red y gestión de servicios no bloquean el compositor.
- Entorno D-Bus/Wayland, audio de usuario y retirada de capacidades heredadas
  innecesarias antes de iniciar procesos gráficos.

**Aceptación:** una secuencia de abrir app → Inicio → volver a app → cerrar app
restaura foco; matar el shell permite recuperarlo; teclado/mando no dejan el
sistema sin salida. No configurar autologin durante el desarrollo inicial.

## H5 · Interfaz Rust con referencia Fire TV 2026

Comprobado en esta VM: shell Wayland interactivo SCTK con tiny-skia/fontdue. Probados desde
TTY a 1920×1080: pulsación larga y Menú nativo, favoritos/orden/ocultación,
búsqueda física y en pantalla, Foot con entrada real, recientes, Inicio/Volver,
volumen/silencio PipeWire y radio Wi-Fi, con restauración de valores. La sesión
funciona con creación de sockets IPv4/IPv6 denegada y sin iniciar Android.
Se verificó carga de preferencias después de reiniciar el shell y alternativas
para iconos dañados, junto con PNG/SVG válidos. Evidencia en reports/h5-interactive/.
Comparación visual de cinco elementos documentada en docs/COMPARACION-FIRE-TV.md.
Presentación del shell real verificada a 720p/1080p/4K en backend anidado,
con capturas cliente/salida coincidentes. 4K nativo no está anunciado por esta VM.
El recorrido completo también pasa sobre DRM nativo a 1280×720; evidencia
en reports/h5-interactive-720/. El renderer aislado tiene medidas a
720p/1080p/4K; esas medidas no son rendimiento del shell completo. Mando físico
y rendimiento/estabilidad del producto pertenecen a H7.


Primero elegir la biblioteca de dibujo/texto y medir un prototipo. Evaluar
Smithay Client Toolkit y buffers SHM como ruta sencilla, sin asumir que Smithay
incluye un toolkit de tarjetas y texto.

- Navegación superior, destacado con fondo/degradado y filas horizontales.
- Descubrimiento de aplicaciones desktop, iconos locales y favoritos persistentes.
- Recientes, reordenación, ocultación y restauración de foco por fila.
- Búsqueda con teclado en pantalla y soporte de teclado físico.
- Ajustes de audio/red, estado de Android y cierre de sesión accesibles con mando.
- Imágenes cargadas fuera del hilo de interacción, caché acotada y alternativa
  legible ante iconos dañados o ausentes.
- Diseño escalable con validación 720p/1080p/4K en las plataformas compatibles.

**Semejanza:** utilizar una captura principal de la nueva interfaz y comparar
pantallas normalizadas a igual resolución, jerarquía, proporciones, foco y
recorridos del mando. Las medidas y tiempos se extraerán de las referencias;
no declarar igualdad píxel a píxel sin una comparación.

**Aceptación:** desde el sofá se pueden abrir aplicaciones, buscar, organizar
favoritos, ajustar volumen y volver al inicio sin ratón. Persistencia tras
reiniciar, foco siempre visible y ninguna función mostrada como operativa si
su integración no existe. El inicio funciona sin red y sin Android arrancado.

## H6 · Aplicaciones APK completas sobre Linux

Aceptación vigente: APK reales de la matriz, con versión/hash y ABI registrados,
ejecutan lanzamiento, interfaz, entrada, persistencia, servicios necesarios y
cierre en Rust/Smithay sin Waydroid ni arrancar Android completo. La inspección
estática y las fixtures son evidencia parcial; no cierran H6 ni A3–A4.
Aislamiento, consumo, recuperación y estabilidad siguen siendo requisitos.

El desglose del runtime está en [ROADMAP-A.md](docs/ROADMAP-A.md); el estado
verificable y la siguiente acción se mantienen en [ESTADO.md](docs/ESTADO.md).

### Laboratorio histórico Waydroid (no aceptación vigente)

El siguiente texto conserva los ensayos y criterios del backend anterior; no
ordena volver a instalarlos ni acredita el runtime APK actual.


En curso. Tras ampliar la VM a 7,7 GiB, sys.boot_completed=1 se observó a los
79 s y se capturó el escritorio Android sobre DRM/Pixman. En sesión combinada,
el shell inicia Android desde ajustes y lanza el VLC oficial x86_64 desde su
búsqueda; Inicio y reanudación pasan con uinput. Evidencia en reports/h6-boot-probe/
y reports/h6-integration/. Se observó un ANR de System UI. Las pruebas multimedia
siguen incompletas: primeros frames decodificados, reproducción detenida y sin
audio continuo demostrado. Persisten pruebas de red externa, IME, recuperación
y suspensión; el hito no está cerrado.

- Confirmar Binder en el kernel y completar el arranque Android: no basta con que
  el contenedor informe RUNNING. Registrar imagen, kernel y sys.boot_completed.
- Validar superficies de Waydroid, buffers SHM/DMA-BUF según el perfil, formatos,
  sincronización, escala y entrada.
- Instalar un APK compatible de prueba y lanzarlo desde el shell; incluir sus
  accesos directos y diferenciar estados preparado, arrancando y error.
- Probar Inicio/Volver, teclado en pantalla, red, audio, vídeo, reinicio y suspensión.
- Comprobar ausencia/fallo de Android sin afectar a las aplicaciones Linux.

**Aceptación:** arranque completo y una aplicación Android útil, entrada por mando,
audio/vídeo y regreso al shell demostrados en cada plataforma soportada. Medir
Android por separado y junto a la sesión. ARM, Google Play y DRM se evalúan
independientemente; no son consecuencias automáticas de usar Waydroid.

## H7 · Ligereza, estabilidad y accesibilidad

Presupuestos iniciales de ingeniería, **no resultados medidos**. Revisarlos al
terminar los ensayos gráficos y documentar cualquier cambio:

| Métrica | Objetivo inicial | Cómo medir |
| --- | --- | --- |
| Memoria compositor + shell | PSS combinada ≤ 120 MiB en reposo a 1080p. | Procesos aislados, caché estabilizada; GPU registrada aparte. |
| CPU en reposo | < 1% de un núcleo durante 60 s sin animación ni entrada. | Medir los procesos de sesión, separando compilación, Codex y Android. |
| Respuesta al mando | p95 < 100 ms de evento local a frame presentado. | Marcas de entrada y presentación; no medir solo el callback de teclado. |
| Fluidez | Objetivo 60 fps durante navegación a 1080p. | Tiempos de frame; declarar explícitamente el resultado de la ruta CPU. |
| Arranque caliente | Primer inicio interactivo en ≤ 3 s desde arrancar el compositor. | Separar arranque del SO, shaders/caché fría y Android. |
| Estabilidad | 2 h de uso, 20 arranques y 50 ciclos abrir/cerrar apps sin fallo. | Logs, memoria antes/después y ausencia de procesos/socket huérfanos. |

También: contraste, etiquetas accesibles, texto legible, foco que no dependa solo
del color, movimiento reducido, pruebas con mandos físicos y desconexiones.
Si un presupuesto falla, registrar causa y optimizar antes de añadir efectos.

**Aceptación:** informe reproducible con hardware, versiones y limitaciones; las
afirmaciones de ligereza y compatibilidad se limitan a plataformas medidas.

## H8 · Paquetes y actualización

Dos revisiones se compilaron en raíces Arch limpias; la segunda pasó diez
pruebas. Su empaquetado se reanudó con --repackage tras una interrupción al
entrar en fakeroot, conservando binarios y fuentes. El ciclo entre r14 y r22
(instalar, actualizar, volver a r14 y retirar) pasó en una raíz Arch base sin
compiladores y conservó preferencias. Se registran hashes, dependencias e
inventario Cargo. Pendientes: cierre de cinco avisos de licencia ausentes,
revisión de condiciones transitivas, reproducibilidad binaria y aceptación
completa de la sesión instalada con usuario normal. Ver docs/PAQUETES.md.

- Paquetes separados para compositor, shell y archivos de sesión.
- Build limpio, Cargo.lock, revisión de dependencias/licencias y fuentes verificadas.
- Separar compiladores y herramientas de prueba de la imagen de ejecución.
- Registrar paquete, fuentes, checksums, inventario y dependencias efectivas.
- Instalar, actualizar, conservar configuración personal y desinstalar en una
  máquina limpia. Definir migración de esquema y recuperación de fallos.

**Aceptación:** sesión seleccionable instalada con pacman sin pasos manuales
ocultos, actualización y retirada comprobadas, receta y fuentes reproducibles.

## H9 · Distribución Arch TV

La ISO de laboratorio corregida se construyó, tiene hash registrado y arrancó
con OVMF/UEFI en QEMU TCG. Llegó al login LTS; desde root live abrió la sesión
DRM/Virtio, lanzó Foot desde el shell y volvió con Home. Un fallo inicial de
initramfs se conservó separado y se corrigió. El ajuste posterior de zona
horaria UTC solo está generado. Pendientes: instalador, usuario normal, arranque
desde disco, aplicación Android, actualización/recuperación y hardware físico.
Ver docs/DISTRIBUCION.md y reports/h9-uefi-boot/. H9 continúa abierto.

- Perfil archiso basado en los paquetes propios, sin datos ni credenciales de la VM.
- Política de versiones/snapshots, kernel y componentes del runtime APK fijados.
- Arranque e instalación UEFI, elección explícita de disco, usuario, idioma y red.
- Definir distribución, procedencia y licencias del runtime APK sin imagen Android completa.
- Actualización, recuperación y documentación para máquinas nuevas.

**Aceptación:** instalar desde una ISO con hash registrado en una VM vacía,
arrancar desde disco, abrir aplicación Linux y Android, actualizar y recuperar
la sesión tras un fallo. Repetir en el hardware físico declarado compatible.

## Evolución A · compatibilidad APK mínima sobre Linux

El usuario precisó el objetivo: estudiar AOSP y reproducir/reutilizar las partes
mínimas para ejecutar APK estables en Linux, sin Waydroid ni un sistema Android
completo. La ampliación del adaptador Waydroid se detuvo. La APK propia ya ejecuta
su DEX en ART host con recursos, listener y preferencias del subconjunto mínimo;
la siguiente acción es conectar su árbol View y la entrada a Wayland/Rust.
[docs/ROADMAP-A.md](docs/ROADMAP-A.md) recoge las etapas y pruebas; los resultados
H6 del laboratorio Waydroid no acreditan esta capa. Se mantienen las validaciones
funcionales, de estabilidad, rendimiento e instalación del proyecto.

## Regla para cerrar un hito

Cada hito requiere implementación, pruebas y evidencia. Un documento, un binario
que solo imprime texto, un paquete instalado o un contenedor RUNNING no acreditan
por sí mismos un compositor, una interfaz o Android funcionales.

La prueba A2 ya representa el árbol en Wayland y verifica uinput, cierre y
reapertura persistente. La siguiente acción es estudiar el port del framework
original AOSP a Linux y mantener esta prueba como regresión. Las demás puertas
del proyecto permanecen abiertas y documentadas.
