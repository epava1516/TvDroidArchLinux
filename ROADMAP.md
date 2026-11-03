# Roadmap · Arch TV nativo en Rust

Prioridad211: [estado canónico](docs/ESTADO.md) · Mapper y contexto GLES software avanzan; HWC bloquea en socket Wayland. Integrar endpoint/peer/FDs específicos y probar presentación real en Smithay, luego display, Zygote y Markor bajo MAC. R1-MAC y compatibilidad amplia siguen abiertos.

Histórico179: [estado](docs/ESTADO.md) · builtin/VDC original alcanza vold y falla25 en auxiliar NNP; exigir operación user0 completa y APEX en vivo, luego Markor bajo MAC. [Evidencias](reports/android16-package-bootstrap/original-apex-derive-mac-progress.json).

Histórico175: [estado canónico](docs/ESTADO.md) y [experimento integrado](reports/android16-package-bootstrap/original-apex-derive-mac-progress.json). Derive original bajo MAC probado; aconfig/proc y verificador bloquean la siguiente integración. R1-MAC y recorrido completo bajo controles abiertos.

Estado de seguridad171 · [admisión original en enforcing y límites](reports/android16-package-bootstrap/r1-mac-integrated-progress.json): Rust→Bionic/init y exec originales de vold/apexd superan NNP1; cgroups privados tienen etiquetas originales y los del anfitrión conservan las Linux. El cliente de inventario APEX falla: UID0/SID shell no puede escribir en la captura UID2000:GID1000/0750 sin capacidades DAC prohibidas. No se acepta disponibilidad APEX ni Markor bajo MAC. El anfitrión queda permisivo/policyload6, auditoría0 y sin procesos/dispositivos propios.170 no pierde auditoría;171 pierde16 registros, por lo que no es exhaustivo. Próximo: identidad/captura legítimas del cliente y derive_classpath original, interfaces Linux de metadatos y logd original; no conceder DAC a shell ni fabricar inventario.

Último recorrido APK probado167 · [nota persistente entre cohortes originales](reports/android16-package-bootstrap/persistent-userdata-functional.json): Markor intacta recupera la nota creada en163, conserva21 bytes/SHA636ce55c…, UID10104, inodos y etiquetas CE/DE. PMS reconoce la instalación previa; el proceso2537 muere, el2918 arranca COLD y un único clic Linux reabre el texto en Smithay, sin escribirlo ni conceder permisos. Nativo/exterior0, APEX41 y comprobaciones reales CE/almacenamiento pasan; fallos163–166 conservados. Cierre sin loops/dm/FUSE, VT1/dispositivos restaurados y resultado consumido sin encolar. Alcance: este recorrido Markdown y almacenamiento privado experimental; no reinicio del anfitrión, pérdida de energía, cierre elegante ni actualización general. Próximo: R1-MAC de la cohorte completa; permisivo no acredita autorización/aislamiento. Producto, otras APK y ARM/GMS/DRM siguen abiertos.

Histórico · Vigente162 · [recorrido local de Markor probado](reports/android16-package-bootstrap/original-user-unlock-progress.json), sección note_process_reopen162: APK intacta instala/lanza, muestra su UI en Smithay, recibe entrada Linux y guarda21 bytes; el gestor original mata el PID2584, lanza el3743 y el puntero reabre la nota con el mismo texto y SHA d846c828… antes/después. Cierre forzado y persistencia entre procesos dentro de una cohorte: no durabilidad entre arranques, cierre elegante ni todas las funciones de Markor. Ruta real Documents/markor y CAP_KILL original; UID/SID/grupos/NNP1 verificados en permisivo. Cohorte cerrada sin loops/dm/FUSE, VT1/host restaurados y resultado consumido sin encolar. Próximo: datos privados durables y dos cohortes reales; R1-MAC, C2/C4–C7, otras APK, ARM/GMS/DRM e instalación/actualización/distro siguen abiertos.

Histórico · Vigente161 · [nota original guardada](reports/android16-package-bootstrap/original-user-unlock-progress.json), sección note_saved_followup160_161: Markor intacta crea y guarda21 bytes exactos de archtv note c59b66e9 con salto final; lectura real de sólo lectura y SHA16458688… verificadas en el cgroup activo. Función principal acotada aceptada para161. El comprobador apuntaba a Documents, pero la carpeta real es Documents/markor: no ejecutó parada/relanzamiento. Corregir esa ruta y verificar PID anterior/nuevo, reapertura gráfica y bytes; no mover datos para satisfacer el comprobador. Presupuesto manual posterior al arranque300s, arranque máximo300000ms intacto; no es prueba de rendimiento. Cohorte cerrada, VT1 y host restaurados; persistencia, R1-MAC, ARM/GMS/DRM y compatibilidad general abiertos.

Histórico · Seguimiento156–159 · [permisos y entrega de entrada](reports/android16-package-bootstrap/original-user-unlock-progress.json), sección permission_input_followup156_159: las capturas155 muestran permiso apagado y diálogo;156 verifica activación y vuelta al editor. No se demuestra un bloqueo inicial de foco del runtime. Se reutiliza media_rw original1023 para el observador privilegiado.157 pierde secuencia;158 conserva106 eventos consecutivos tras leer ACK antes del timeout, pero sigue truncando el nombre: no hay nota esperada ni cierre/reapertura.159 usa WAIT_FOR_FINISH original2 y se detiene correctamente sin escribir al no alcanzar Main; no hay nota/ciclo probado.160 reutilizará el mismo artefacto con permiso verificado visualmente. APK/permisos intactos, MAC permisivo y durabilidad/ARM/GMS/DRM abiertos.

Histórico · Seguimiento154/155 · [nota y ciclo de proceso](reports/android16-package-bootstrap/original-user-unlock-progress.json), sección saved_note_lifecycle_followup154_155:154 lee el texto esperado mediante el cliente original, pero falla al crear evidencia por DAC;155 prepara esos archivos, pero no alcanza el editor tras permisos y termina con pantalla negra/estado dormido. Causa inicial desconocida; no se aceptan guardado, cierre ni reapertura. InputDispatcher registra falta de ventana/canal antes del timeout de energía, que ocurre después. Próximo: retorno original de permisos y foco/ciclo de actividad; el conductor debe detenerse si no alcanza el editor. Conservar153 como prueba acotada, no garantía de repetibilidad. Ambos cierres restauran VT1/dispositivos, sin loops/dm/FUSE; notificaciones consumidas sin encolar. R1-MAC, ARM/GMS/DRM y durabilidad entre cohortes abiertos.

Prioridad153: [bytes guardados→cierre de proceso→relanzamiento→reapertura real](docs/ROADMAP-A.md). Trust original permite editor y texto por teclado Linux; [evidencia153](reports/android16-package-bootstrap/original-user-unlock-progress.json). Guardado todavía sin lectura válida, C3 y durabilidad abiertos; R1-MAC, ARM/GMS/DRM y producto siguen en el objetivo.

Camino crítico desde132: [cierre coherente y almacenamiento/OverlayManager originales](docs/ROADMAP-A.md) → UI/entrada/nota/cierre/reapertura de Markor. El usuario ya alcanza RUNNING_UNLOCKED y AMS lanza la APK intacta hacia IntroActivity; falta aceptación del recorrido completo. R1-MAC, ARM/GMS/DRM abiertos.

Camino crítico desde129: [preparación CE original vía vold](docs/ROADMAP-A.md) → RUNNING_UNLOCKED real → Markor completa. El ciclo original LSS ya crea la contraseña sintética y abre claves CE; eso no acredita almacenamiento preparado ni cifrado en reposo. Lanzamiento, UI, entrada y persistencia siguen abiertos.

Camino crítico desde127: [integrar el ciclo original restante de LockSettings](docs/ROADMAP-A.md) → desbloqueo real del usuario → Markor completa. Instalación intacta conservada; lanzamiento, UI, entrada y persistencia no aceptados. R1-MAC permanece abierto.

Camino crítico: [plataforma conjunta GateKeeper/Keystore/JCA/PMS122](docs/ROADMAP-A.md) → resolver la espera original de start-user → RUNNING_UNLOCKED → lanzamiento/UI/entrada/nota/cierre/reapertura de Markor. Instalación intacta repetida, sin lanzamiento aceptado. R1-MAC sigue abierto.

Camino crítico actualizado: integrar [JCA original120](reports/android16-package-bootstrap/keystore-java-functional.json) con GateKeeper y servicios originales → RUNNING_UNLOCKED → Markor. La fase1000 original de103 se conserva. Véase la puerta de decisión y criterios en [ROADMAP-A](docs/ROADMAP-A.md).

Actualización 2026-11-02 · [Usuario y ciclo APEX originales](reports/android16-package-bootstrap/original-user-unlock-progress.json):103 conserva APEX41 y atraviesa fase1000, incluyendo MediaSession/MediaCommunication y StagingManager originales. La salida lazy normal de apexd ya no cierra la cohorte; reinicio bajo demanda aún no probado. UserController llega a LockSettings y espera GateKeeper original, cuyo ctl.interface_start está rechazado. Siguiente: integrar gatekeeperd y sus backends reales de seguridad; después comprobar RUNNING_UNLOCKED y lanzar Markor, sin fabricar credenciales, claves ni flags. No hay lanzamiento/UI/entrada/nota persistente aceptados. R1-MAC permisivo, cierre interno y ARM/GMS/DRM abiertos.

Histórico 2026-11-02 · [Ciclo original de bootanimation](reports/android16-package-bootstrap/bootanimation-lifecycle-functional.json):101 acepta su salida CLD_EXITED0 sólo con service.bootanim.exit=1 original. La cohorte permanece viva y AMS supera la llamada original de checkpoint; el error anterior era posterior al cierre provocado por el coordinador. Settings.FallbackHome llega a Displayed con IMMS original. El bloqueo demostrado pasa a fase1000: MediaSessionService requiere MediaCommunicationService ausente. Siguiente: integrar ese subsistema original y observar desbloqueo real, retirar HOME mediante PMS y lanzar Markor. Ningún lanzamiento/UI/entrada/persistencia de Markor aceptado; R1-MAC permisivo, cierre interno y ARM/GMS/DRM abiertos.

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
| H6 | APK completas sin modificar sobre Linux, sin Waydroid ni imagen Android arrancada. | H5, R0–R7 | Pendiente; laboratorio Waydroid histórico |
| H7 | Rendimiento, estabilidad y accesibilidad medidos. | H5, H6 | Pendiente |
| H8 | Paquetes propios y sesión instalable. | H7 | Parcial histórico; runtime APK sin empaquetar |
| H9 | Imagen Arch TV e instalación desde cero. | H8 | ISO de laboratorio; instalación/recuperación pendientes |

## Runtime vigente · A16-QPR2-1

H6 se rige por [el contrato](docs/CONTRATO-APK.md) y las puertas
[R0–R7](docs/ROADMAP-A.md): Android16 QPR2 como base, Bionic/AOSP original sobre
Linux, SurfaceFlinger→Wayland como primera hipótesis y Smithay manteniendo el
control del escritorio anfitrión. ART host/glibc y API33 conservan evidencia
histórica, sin fijar la base nueva ni prohibir servicios originales individuales.
No se arranca Android completo ni se reinicia VM/cliente para este contrato.

La secuencia de seguridad posterior al arranque permisivo está en el
[plan canónico](docs/ARQUITECTURA.md#plan-de-seguridad-y-recuperación-del-anfitrión):
recuperación/contrato offline/preflight antes de pedir carga, y enforcing con
autorización separada. Kernel activo o Binder con SID no cierran R1-MAC.

La vertical inicial es Markor completa; después categorías distintas, incluidas
Android TV/mando, sin adaptaciones particulares por APK. La matriz registra nueve
etapas, API/servicios externos, ABI e ISA/32/64 por separado. GMS/microG, WebView,
media/DRM y OEM no se dan por resueltos por identificar interfaces. CDD/CTS son
referencias, no certificación por un subconjunto. H7 mide todos los procesos y
servicios con presupuestos justificados por hardware/resultados; H8/H9 añaden
APK/splits/firmas/ABI, migración/desinstalación, runtime reproducible, mantenimiento
de seguridad, instalación limpia y rollback. No recortar comportamiento para
aparentar ligereza o compatibilidad.

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

Para A16-QPR2-1 se medirán también runtime y servicios completos. Los umbrales
del shell que siguen son objetivos heredados del laboratorio; contrastarlos con
hardware/resultados y documentar los presupuestos de la nueva base, sin suprimir
comportamiento. Ninguna cifra antigua acredita ligereza del runtime A16.

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
