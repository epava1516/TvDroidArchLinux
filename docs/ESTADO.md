# Estado actual y punto de entrada

Vigente: contrato **A16-QPR2-1**, recibido el 2026-10-30. Sustituye BASE-AOSP-1 en
base, estrategia nativa y prioridad gráfica. Git y artefactos prevalecen sobre
los resúmenes; no se ha completado compatibilidad amplia.

## Retomar

1. [Checkpoint](../reports/android16-zygote-security-contract/checkpoint.json) y contraste con
   Git/procesos/artefactos según [CONTINUIDAD.md](CONTINUIDAD.md).
2. [Contrato íntegro vigente](CONTRATO-APK.md), [arquitectura](ARQUITECTURA.md),
   [roadmap APK](ROADMAP-A.md) y [general](../ROADMAP.md).
3. [Matriz real](COMPATIBILIDAD-APK.md) e [índice de evidencias](EVIDENCIAS.md).
4. Continuar R0→R1 sobre Android16 QPR2 nativo, sin ampliar API33 por métodos.

Investigación R6 independiente: [traducción ARM y opciones existentes](TRADUCCION-ARM.md).
No habilitada ni bloqueante del avance x86_64; el checkpoint principal anterior
sigue siendo el punto de recuperación del runtime.

## Revisión vigente · aislamiento original de zygote

[Fuente y límites](../reports/android16-zygote-security-contract/findings.json):
zygote instala seccomp antes de perder capacidades y documenta la tensión entre
NNP y transiciones SELinux. En permisivo omite filtros de aplicación/sistema y
UID/GID en las ramas examinadas. No hay ejecución nueva ni aislamiento acreditado.
Evaluar NNP heredado frente a una cohorte privilegiada acotada con frontera de
aplicación original; ninguna alternativa seleccionada ni implementada todavía.
Inventariar todas las identidades, capacidades, FD, dispositivos y cgroups antes
de otra variante de política. Markor sigue sin etapas aceptadas.

## Avance vigente · bootstrap original, sólo offline

[Resultados](../reports/android16-launcher-bootstrap/findings.json) y
[checkpoint](../reports/android16-launcher-bootstrap/checkpoint.json): cuatro
variantes compilan con aserciones activas; 51 consultas originales verifican
21 cálculos/permisos y 30 denegaciones. El prefijo creador→supervisor Rust→init
conserva las identidades previstas. Seis consultas NNP/nosuid de los gestores
siguen denegadas; no hay cadena completa disponible ni ejecución etiquetada.
La fuente kernel de referencia muestra que «kernel» antes de cargar política
puede representar INIT: el modelo usa linux.init_t, sin afirmar su SID real.
El ejecutable de entrada no puede crearse, modificarse ni reetiquetarse mediante
los permisos del candidato; procedencia, instalación y confianza del inode siguen
sin demostrar. El supervisor Rust debe crear el canal como padre, después de la
preparación privilegiada. R1-MAC y las nueve etapas de Markor siguen abiertas.

## Auditoría anterior · herencia y productor del lanzador

[Resultados](../reports/android16-launcher-permission-audit/findings.json): export
original completo152.494 AV/657 xperm;54 reglas potenciales de salida,633 de entrada,
ninguna xperm del actor. No equivalen a concesiones efectivas. Veintisiete consultas
libsepol: capacidades administrativas/UID examinadas denegadas; urandom condicional
denegado por defecto, lockdown/execmod heredados permitidos offline sin justificar
necesidad. Tres dominios Linux de control pueden ptrace en esa capa; no prueba
syscall/DAC/capabilities ni aislamiento de administrador anfitrión. Actores Linux
examinados no pueden entrar al rol. Módulos y perfil base intactos; no carga/labels.
Siguiente: entrada por ejecutable/tipo/rol original con productor explícito y
preparación previa, sin permisos globales ni bootstrap supuesto. R1-MAC y Markor
siguen abiertos; export/delta grande enlazado por ruta/hash, no pegado al resumen.

## Último experimento · rol exclusivo y exec Android explícito

[Resultados offline](../reports/android16-policy-launcher-entry/findings.json):
variante automática calcula Linux.system_u/Linux.system_r/init y el contexto del
siguiente gestor no es válido. Candidato explícito usa rol nuevo exclusivo y
u:r:init:s0; compila con aserciones activas, conserva transiciones originales de
servicemanager/hwservicemanager y permite interfaces seleccionadas del coordinador.
Niega bypass de gestor, dyntransition, escritura del ejecutable, pérdida MCS,
administración de política y accesos app examinados. Cuatro sujetos Linux de
control mantienen denegación antes/después. Error de rol inválido no es denegación.
Excepción de constraint limitada al nuevo actor: adaptación propia explícita.
Perfil base intacto; sólo experimento, sin proceso/contexto/label asignado ni carga.
Faltan bootstrap real de host, permisos heredados y cierre de interfaces/recuperación;
S0–S2, R1-MAC, gestores y Markor siguen abiertos. Handles de este experimento terminales.

## Retoma actual · requisitos de host y montaje original

[Contraste y ejecución](../reports/android16-postboot-mac-readiness/findings.json):
Git y origin consultado coinciden al inicio en1407908; seis pendientes anteriores
con hashes conservados. Checkpoints/evidencias anteriores verificados; nueve
pruebas de2f31032 pertenecen al comprobador, no a MAC/APK. Handles preboot históricos.
Kernel actual activo/permisivo/policyload0. REA nativo UID10000/caps0 obtiene kernel
como contexto y ENODATA en ejecutable; status original mmap0 sólo tras API explícita
sobre montaje genuino RO. Autodetección rechaza RO por diseño. Clases consultadas0.
Fuente/exports REA separan ABI Android de cabeceras genéricas. Anfitrión systemd
-SELINUX y sin libselinux instalado: integración pendiente, no inferida del LSM.

Orden y criterios de autorización únicos en el [plan canónico](ARQUITECTURA.md#plan-de-seguridad-y-recuperación-del-anfitrión).
No cargar, reetiquetar, activar enforcing ni reiniciar; completar entrada/mediación,
recuperación y preflight, continuar experimentos independientes y luego gestores
originales/Markor. No se repitió Binder ni se alteró matriz de APK para aparentar avance.

## Última evaluación · falta la entrada Linux al coordinador Android

[Resultados offline](../reports/android16-policy-launch-transitions/findings.json):
libsepol original conserva tres transiciones Android seleccionadas, pero el
candidato deja los dominios Linux examinados sin cambio al calcular contexto para
init_exec/servicemanager_exec. El init Android tampoco puede usar selinuxfs con
etiqueta Linux (compute_create/compute_av y accesos de archivo denegados).
Doce cálculos de contexto y doce consultas de acceso; errores de contexto
separados de denegaciones. No se cargó ni amplió política. Compilación anterior
no acreditaba entrada al runtime; diseñar lanzamiento y mediación juntos antes
de despliegue. Arranque permisivo y compatibilidad APK siguen sin equivalencia.

## Arranque actual · LTS con SELinux permisivo, sin política

[Verificación posterior al reinicio autorizado](../reports/android16-selinux-permissive-boot/findings.json):
LTS6.18.59, LSM SELinux activo, enforce0, policyload0 y policyvers35 soportada.
Contexto inicial kernel, sin dominios Android. Selinuxfs no montado en el host;
sólo se montó en privado/lectura para comprobar estado y sonda. Comprobador
corregido para página virtual de tamaño cero, nueve pruebas y lectura real pasan.
Mismo ELF Binder que antes: control y petición SID ahora completan transacción y
respuesta0, con BR_TRANSACTION_SEC_CTX/PID/UID observados. No se lee el texto del
SID ni se acredita identidad/MAC. Resultados previos «LSM inactivo / SID-95» son
históricos de otro arranque. Todos los handles pre-reinicio son históricos.
R1-MAC sigue abierto: política, etiquetas/transiciones, enforcement, denegaciones,
gestores originales y aislamiento no probados. No se cargó política ni se cambió
el modo; selección de arranque sólo para esta vez, revalidar tras otro reinicio.

## Última integración · fallos originales entregados a Rust

[Pruebas](../reports/android16-linux-failure-sink/findings.json): trigger_shutdown
original tiene receptor Linux serializado, sin ejecutar la petición. Service::Start
falla getcon y su reboot_on_failure llega como fallo tipado; Rust recoge salida
real69, wrapper1, sin ACK de arranque. Petición mayor de24 bytes falla explícitamente;
no se trunca como válida. Worker diagnóstico conserva arranque/cierre0;17 pruebas
Rust, clippy y check compositor pasan. Ensayo inicial de argumento inválido
conservado aparte. No cubre LOG(FATAL)/critical, monitor asíncrono, watchdog,
recovery, MAC ni servicio/APK disponible. Siguiente: política de cohorte y controles.

## Última frontera · efectos de perfiles originales auditados

[Resultados](../reports/android16-service-effect-audit/findings.json): observador
delega los parsers AOSP, conserva tokens/archivos/líneas y separa declaraciones
históricas de campos públicos finales tras override. Cuatro servicios y una acción
originales inspeccionados; ninguna acción/servicio ejecutado ni admisión aprobada.
MCP verifica comillas/import/override y rechazo de opción inválida sin manifiesto.
Referencias directas aún fuera de cohorte: apexd, audioserver, gatekeeperd y
surfaceflinger; clases main/hal/early_hal requieren alcance Linux explícito.
No suprimir onrestart/critical ni considerar suficiente que un parser acepte RC.

## Último contraste · Start original rechaza falta de contexto

[Prueba y alcance](../reports/android16-service-start-gate/findings.json): perfil
servicemanager original en ServiceList global; llamada nativa Service::Start
devuelve «Could not get security context» antes del fork. REA MCP confirma PID0,
no running, waitpid ECHILD y FD4→4. Éxito de prueba negativa, no servicio lanzado.
No usar seclabel inventado para saltar R1-MAC. Start modifica flags antes de fallar;
otros perfiles con reboot_on_failure pueden disparar shutdown incluso en error
temprano: requieren política Linux explícita antes de admitirlos.

## Última integración · SIGCHLD original antes de los workers

[Resultados](../reports/android16-child-reaper/findings.json): descriptor original de
SIGCHLD y ReapAnyOutstandingChildren integrados en el bucle Bionic antes de crear
hilos. REA MCP: getprop0/false1 recogidos, waitpid ECHILD para ambos, máscara
restaurada y FD4→4; worker bajo Rust arranca y cierra con salida0. Una sola vida
por proceso; reinicio requiere proceso nuevo. Hijos sin ServiceList: no acredita
Service::Reap registrado, restart, cgroups, cierre de descendientes ni APK.
Siguiente: backend Linux de servicios/controles; R1-MAC sigue pendiente.

## Último preflight · perfiles originales de servicios

[Resultados y límites](../reports/android16-service-profile/findings.json): parser
AOSP nativo UID10000/caps0 acepta cuatro RC originales en rutas de instalación;
perfiles de sistema coinciden con GSI, vendor sólo preparado, no instalado.
Opciones/arity inválidas y archivo ausente devuelven2. read_ok puede ser1 con
parse_errors1 y ServiceList parcial: no promover ese resultado a perfil activo.
No se ejecutan servicios/acciones ni CheckAllCommands con mapa runtime; valores de
builtins no comprobados. Fuente exige SIGCHLD antes de hilos y diferencia Start de
readiness. Pendientes identidad Android1000 vs host1000, contextos/cgroups/perfiles,
fallos críticos/onrestart y backend Linux real; ninguna etapa APK aceptada.

## Integración anterior · supervisor Rust y worker Bionic

[Implementación y pruebas](../reports/android16-rust-supervisor/findings.json):
archtv-core posee Child/pidfd y canal Unix heredado; worker Bionic reutiliza
propiedades/acciones/cierre originales adaptados. REA MCP observa modo diagnóstico
arrancar→STOP→confirmación→salida real0. Modo normal se niega sin SELinux activo,
sin confirmar arranque. No estado de runtime/APK listo por ese handshake.
Pasan6 pruebas previas y7 de protocolo, check del compositor y clippy core.
Ejecutor interno de ejemplo; no servicio instalado ni integración completa con
compositor. Pendientes backend ctl/servicios, restart/watchdog/recuperación, MAC,
instalación/actualización y recorridos APK. Cierre forzado puede esperar I/O kernel;
plazos del protocolo no acreditan un watchdog completo.

## Integración anterior · coordinador nativo de acciones

[Parche y pruebas](../reports/android16-property-actions/findings.json): entrada
Linux explícita reutiliza eventfd/ActionManager y callbacks originales sin cargar
boot scripts ni SecondStageMain. MCP0: cambio persistente real dispara acción
programática, expansión original y archivo; cierre con acción pendiente devuelve
error hasta procesarla. Inicio duplicado/Epoll ajeno/poll tras cierre rechazados;
hilos4→1/FD4→4. Comandos propios de regresión, no mapa builtin/RC ni compatibilidad APK.
Modo opt-in rechaza ctl/power sin backend tras permisos originales; rechazo de esos
controles sólo fuente/compilación, no petición autorizada. Siguiente: backend real
de servicios/controles y supervisor Rust por frontera explícita; R1-MAC pendiente.

## Adaptación anterior · cierre del servicio de propiedades

[Parche y pruebas](../reports/android16-property-shutdown/findings.json): API local
StopPropertyService despierta receptores, une hilos y cierra recursos propios;
writer/restorecon dejan de depender de hilos sin cierre coordinado. Cadena de dos
parches reproduce exactamente el overlay desde archivo AOSP verificado.
MCP0 idle y petición incompleta: hilos4→1/FD4→4, sockets ausentes, descriptor del
coordinador conserva ownership y retorno normal del servidor. Timeout original de
petición5000ms observado; cierre5006ms, sin plazo garantizado ante I/O bloqueado.
No colas de escritura/restorecon activo probadas, callbacks/ctl integrados, MAC,
APK o supervisor completo aceptados. Reinicio requiere proceso nuevo.

## Fase anterior · carga original de persistentes

[Prueba](../reports/android16-property-load/findings.json): StartPropertyService
recibe InitMessage original, carga valor del protobuf y publica él mismo
ro.persistent_properties.ready=true. La espera de seriales Bionic detecta el cambio;
no se escribe la señal manualmente. MCP0, con rechazos DAC/contexto conservados.
No reinicio de servidor, permisos MAC, readiness de gestores ni APK aceptados.
El canal de carga no transporta callbacks/controles actuales: se llaman directamente
al bucle de init; campos proto stop/start sin rama implementada. Siguiente: frontera
Linux explícita de callbacks/control/cierre, sin asumir que el socket la resuelve.

## Ejecución anterior · servidor de propiedades y rechazo real

[Prueba por socket](../reports/android16-property-socket/findings.json): se ejecutan
PropertyInit y StartPropertyService originales con parche de persistencia; dos
sockets/hilos arrancan en namespace privado. Cliente exec UID10000/caps0/NNP1:
socket system denegado EACCES; socket general responde0x18 al fallar getpeercon
(Protocol not available), Bionic retorna-1 y la propiedad queda ausente. MCP salida0
es éxito del diagnóstico negativo, no disponibilidad/MAC ni escritura autorizada.
Inicializador root con capacidades; cierre por _exit diagnóstico, no supervisor de
producción ni shutdown ordenado. Pendientes callbacks/ctl/carga persistente y R1-MAC.

## Adaptación anterior · errores de persistencia

[Parche y pruebas](../reports/android16-property-errors/findings.json): adaptación
local de tres archivos AOSP, fuente original intacta. API TryWritePersistentProperty
propaga errores; llamadores síncrono/asíncrono compilan/enlazan con respuesta de fallo.
REA MCP observa positivos y EACCES real, más EIO explícitamente inyectado en fsync
archivo/directorio. Tras fallo de directorio post-rename hay dato visible y error,
sin prometer rollback/durabilidad. Parche aplicado sin fuzz reproduce el overlay.
ACK real por socket, ENOSPC/rename/crash, supervisor y MAC siguen pendientes.
No runtime instalado ni etapa APK aceptada.

## Regresión anterior · persistencia original

[Prueba positiva y negativa](../reports/android16-persistence-native/findings.json):
REA MCP observa salida0 al escribir/actualizar con funciones originales y leer
valores desde execs separados. Directorio0555 bajo UID10000: escritura directa
retorna EACCES; WritePersistentProperty void registra fallo y retorna; lectura
posterior conserva valor previo. No servidor/socket ACK, reinicio de servicio,
pérdida de energía ni persistencia APK aceptados. Siguiente: adaptación acotada
para propagar errores reales, comprobar fsync/rename/ENOSPC y conservar subsistema
original; supervisión y R1-MAC siguen pendientes.

## Análisis anterior · servicio de propiedades original

[Clausura y límites](../reports/android16-property-service-closure/findings.json):
retener StartPropertyService enlaza sin ejecutar Android init;268 símbolos definidos
adicionales, SecondStageMain ausente. No se ejecutó el candidato: su entrada sigue
llamando sólo PropertyInit. La fuente exige sockets, credenciales/SID/MAC, epoll,
mensajes de carga persistente y callbacks reales al supervisor. PropertyChanged ya
estaba en el enlace anterior; no se atribuye al nuevo delta.
La fuente no propaga todos los fallos de escritura persistente al ACK; falta probar
RO/ENOSPC/fsync/rename y recuperación antes de aceptar durabilidad. Siguiente:
frontera mínima explícita con supervisor Linux, sin ejecutar init completo ni
responder éxito a controles ausentes. R1-MAC y toda compatibilidad APK siguen abiertos.

## Diagnóstico anterior · hwservicemanager original

[Resultado](../reports/android16-hwmanager-start/findings.json): binario GSI original,
UID/GID1000 y grupos system/readproc según RC, Binder privado separado. REA MCP
observa lectura de contextos de servicios y aborto al obtener contexto SELinux propio
(salida127). Falta manifiesto vendor y se registra advertencia libvintf; no son
la causa fatal observada. No registro, readiness ni IPC de gestor aceptados.
Cadena pendiente: LSM/política/etiquetas→servicio de propiedades real→gestor/VINTF→
readiness original→Composer/HAL. No activar readiness manualmente. El host actual
sin SELinux activo y el contrato sin reinicios impiden aceptar esa ejecución aún;
continúa trabajo independiente de configuración/instalación y subsistemas originales.

## Hito anterior · Composer enlazado, espera real de gestor

[Resultados](../reports/android16-composer-link/findings.json): servicio Composer2.1,
recursos y adaptador framebuffer originales compilan/enlazan estrictamente.
REA MCP observa tres dispositivos Binder privados, identidad UID10000/caps0/NNP1,
ausencia de vndservicemanager y espera repetida de hwservicemanager.ready. La prueba
acaba por límite con señal9; no arranque exitoso ni carga HAL acreditada. Un observador
sólo redirige logs reales; no cambia readiness/respuestas. El preflight host de sólo
lectura sigue sin cumplir requisitos. Siguiente prioridad: gestores reales/R1-MAC
y supervisión; no saltar la espera ni cambiar el contrato de arranque.

## Hito anterior · libui enlazada y ejecución acotada

[Resultados](../reports/android16-libui-link/findings.json): libui completa enlaza
estrictamente con proveedores originales GSI y dos dependencias estáticas fuente.
Se corrigió el perfil diagnóstico según Soong original (-fno-rtti); se conservaron
los fallos RTTI previos. REA MCP observa salida0, UID10000/caps0/NNP1 y libui fuente
mapeada: operaciones de regiones, transformación inversa y sentinel NO_FENCE.
No allocator/mapper funcional, fence real, Composer, frames o APK aceptados.
Siguiente: enlace del servicio original y cierre real de dispositivos/buffers;
R1-MAC y recorrido completo Markor siguen pendientes.

## Hito anterior · implementación original libui

[Resultados](../reports/android16-libui-implementation/findings.json): las23 unidades
originales de libui y libui-types compilan sin modificar fuentes. Siete familias
HIDL allocator/mapper generan transportes; diez hashes congelados coinciden.
Allocator AIDL V2 y exports originales permiten compilar Gralloc2–5; un symlink
libsync omitido en la extracción se recupera del archivo original con hash verificado.
No enlace completo, equivalencia Soong/sanitizadores/AFDO, ejecución de buffers,
servicio Composer o APK aceptados. Siguiente: dependencias completas y enlace
estricto antes de probar comportamiento; R1-MAC permanece pendiente.

## Hito anterior · codecs gráficos originales

[Resultados y límites](../reports/android16-libui-source-closure/findings.json):
AIDL construido desde la revisión original con SDK36 genera31 entradas/124 archivos.
Compilan32 unidades Bionic, incluido ComposerResources. Dos bibliotecas de codecs
originales enlazan y una regresión nativa observada por REA MCP termina0: NativeHandle
con FD real y PlaneLayout anidado mediante AParcel; ambas bibliotecas fuente aparecen
mapeadas. Es duplicación local de FD, no transferencia Binder entre procesos.
No libui completo, HAL, buffers gráficos, frames ni APK aceptados.
Siguiente: completar módulos originales libui/allocator/mapper y agrupación HIDL;
R1-MAC sigue pendiente. La matriz real conserva sus nueve etapas no probadas.

## Objetivo y decisiones

APK completas sin modificar, plataforma general con compatibilidad amplia para
aplicaciones arbitrarias/Android TV sobre Linux y compositor Rust/Smithay. Bionic/AOSP
es la vía principal; conservar subsistemas originales completos y sus dependencias.
Primera hipótesis gráfica: SurfaceFlinger original con salida adaptada a Wayland.
No Waydroid ni imagen/distribución Android arrancada, ni VM Android escondida.
No reiniciar **VM ni cliente** bajo este contrato. Servicios originales individuales
no equivalen automáticamente a Android completo; estudiar cierres reales.

| Clasificación | Estado verificable |
| --- | --- |
| Base elegida por contrato | Android16 QPR2/r4, x86_64 primero y diseño ARM64. Tag/rama/build y API verificados en fuentes oficiales. Elección no equivale a implementación funcionando. |
| Procedencia fijada | Manifiesto fuente/derivado y registro de las 1.013 revisiones exactas; reproducción offline y diez objetos principales verificados. GSI oficial x86_64 del mismo build/SDK36.1 verificada; linker, ayuda ART y regresión DEX ejecutados con componentes originales y configuración generada. No equivalencia fuente/binario completa ni R1 aceptada. |
| Se conserva | Compositor/shell Rust, instalación/herramientas y regresiones previas útiles; H7–H9 permanecen abiertos. |
| Históricos Android13 | ART host/glibc y fixtures propias; mezcla de jars/core/JNI; loader Bionic parcial y cierre de bibliotecas. No se trasladan como validación de A16. |
| Pendiente separado | Cuatro archivos propios de JNI/bootstrap host conservados sin commit. Ensayos API33 de propiedades/configuración pausados, sin área ejecutada en esa línea ni cambio a producción. |
| Configuración parcial A16 | Propiedades originales170 leídas sin capacidades. ART original y RuntimeInit.main ejecutados; Binder privado permite llamar ActivityThread.main. Histórico previo al reinicio: gestores bloqueados por SELinux inactivo; estado actual permisivo/sin política descrito arriba, sin APK aceptada. |
| Herramientas | REA MCP respondió realmente; análisis ELF/APK estático previo y estado actual, sin presentarlos como ejecución ni CLI como conexión. |
| No probado | Nueve etapas de las APK sobre A16; SF→Wayland, aceleración/entrada/AV/TV, aislamiento por app/Binder, GMS/DRM/OEM/WebView, traducción ISA/32/64, presupuestos, instalación/actualización/seguridad actualizada. |


## Diagnóstico previo de PropertyInit · superado por el perfil fuente

[Pruebas y alcance](../reports/android16-propertyinit-entry/validation.json):
146 fuentes originales de protobuf/Abseil compilan para Bionic; sus dependencias
cierran el enlace de la entrada supervisada PropertyInit (salida0). Ejecución real
del inicializador original aborta (salida127) por faltar
`/vendor/etc/selinux/plat_sepolicy_vers.txt` en el perfil GSI de sólo sistema.
No readiness, sockets ni APK. El inicializador es UID0 con capacidades root en
namespaces privados; esto no acredita aislamiento de aplicaciones ni SELinux.
Siguiente: contrastar generación y selección original del perfil vendor/política,
sin fabricar valores, omitir comprobaciones o iniciar Android completo.


## Perfil de propiedades y diagnóstico previo de opciones

[Pruebas](../reports/android16-property-profile/validation.json): la regla original
sepolicy_vers y la herencia BP4A derivan el valor202504 del perfil fuente. Con esa
entrada, PropertyInit original retorna0; getprop original lee los mismos170 valores
con UID10000/capacidades0. El inicializador fue UID0, separado del lector. No se
acreditan vendor de hardware, paridad de configuración GSI, sockets ni SELinux.

App_process termina1. REA MCP/GDB observa JNI_CreateJavaVM→Runtime::Create→
ParseOptions→ParsedOptions::Usage→runtime_exit(1): falla al analizar opciones,
antes de disponibilidad de VM. La traza tiene símbolos originales ajustados a
mapeos observados; breakpoint pendiente por sí solo no habría probado esa entrada.
Debugger cerrado e inferior terminado. Próximo paso: estudiar fuentes y lista real
de opciones del arranque; no declarar ActivityThread/Markor ejecutados.


## Puerta vigente: Binder privado y política del Linux anfitrión

[Resultados](../reports/android16-binder-service-gate/validation.json): kernel LTS
6.18.59, Binder Rust integrado y montajes binderfs privados. Dos contextos asignan
dispositivos distintos y responden protocolo8 con UID10000/capacidades0; esto no
prueba transacciones o aislamiento completo. Corrigiendo el conflicto de opciones
del harness, ART original ejecuta RuntimeInit.main y llega a llamar ActivityThread.main
con Binder privado; faltan el gestor de contexto y HIDL. No Markor instalada/ejecutada.

Servicemanager original, con UID/grupos de su rc y sin capacidades, aborta en
selinux_status_open(true). SELinux está compilado pero no está entre los LSM activos.
La [documentación del kernel](https://kernel.org/doc/html/latest/admin-guide/kernel-parameters.html)
describe la selección inicial mediante CONFIG_LSM/lsm=; no confundir una biblioteca
libselinux o un archivo status con política y mediación activas.

Siguiente unidad: integrar la política, etiquetas y transiciones del runtime con
la seguridad del Linux anfitrión, preservando las comprobaciones originales de
servicios. Incluir contextos Binder/HIDL/vendor, gestores, propiedades/VINTF,
identidades por servicio/app y pruebas de registro/descubrimiento/denegación/muerte.
No cargar una política Android aislada como si sólo afectara a una carpeta ni
sustituir comprobaciones por permisos ficticios. El contrato actual impide reiniciar
la VM: preparar y validar fuentes/build/instalación y pruebas independientes;
la activación y enforcement en esta VM quedan pendientes de un arranque permitido.
No se ha cambiado el boot ni arrancado Android.


## Preparación de seguridad · herramienta y compilación offline

[Validación](../reports/android16-host-security-preflight/validation.json): diagnóstico
de sólo lectura, ocho regresiones y comprobaciones con/sin permisos elevados;
la VM no satisface los requisitos de SELinux. Las capturas offline no acreditan
un kernel vivo. Host libsepol/secilc originales construidos; política platform CIL
de la GSI compilada con opciones originales y neverallow activo. Nada instalado,
cargado o reetiquetado, ni host/servicios/APK aceptados. Siguiente: comparar las
bases de política AOSP+Linux y refpolicy+contratos AOSP antes de elegir/desplegar.


## Comparación de bases de política · pendiente de elección

[Resultados](../reports/android16-policy-base-comparison/validation.json): refpolicy
fijada por commit y verificada, baseline Linux MCS/systemd/formato30 compila offline.
Las136 clases y permisos coinciden con el CIL del compilador; AOSP platform tiene107.
Tres clases de registro/propiedades Android faltan en refpolicy. La composición
global sin adaptar falla por role object_r repetido; no prueba imposibilidad de
integración. Siguiente: herramientas semánticas existentes y fronteras de política
antes de transformar. Ningún host reetiquetado, política cargada, reinicio o APK.

## Checkpoint y siguiente acción

Base histórica del diagnóstico de entrada: `e520093`. Contrato y manifiesto publicados; consultar el checkpoint vigente y Git para HEAD/origin actuales. El snapshot local
`/home/tv/recuperacion-archtv/20261031T010916Z-a16-framework-entry` guarda parches,
archivos nuevos y scripts de estudio. Los logs ajenos H9 permanecen intactos.
El checkpoint registra procesos/handles y resultados; no hay ART/bwrap/build activo
observado tras las pruebas A16. No restaurar parches sin contrastar Git.

Siguiente unidad: enlazar/evaluar el prototipo libinit original con un entrypoint
Bionic supervisado por Linux, sin activar second_stage. El inventario de todas
las entradas presentes y su clausura directa de build está en
[la decisión](../reports/android16-boot-profile/unit-decision.json). Las 52 fuentes ya compilan y el archivo prototipo contiene 63 miembros; faltan
dependencias transitivas, callbacks/control reales, persistencia y mediación;
no añadir sólo la propiedad que permita superar el siguiente guard ni duplicar
las derivaciones originales en un mapa propio. No hay nuevo perfil ejecutable.

El build **protoc host** terminó 0 (sesión69923, 393 pasos); su resultado y los
esquemas están en [la validación](../reports/android16-original-protoc/validation.json).
Protoc25.8 original generó los tres esquemas init y sus fuentes compilaron para
Bionic; no relanzar ese build. Siguiente unidad: libinit completo con sus grupos
nativos, cabeceras exportadas y dependencias generadas reales. Los módulos
parciales no acreditan un servidor ni un recorrido APK.

[Avance de dependencias](../reports/android16-native-dependencies/validation.json):
libcap estático original construido, seis fuentes/miembros ELF y generadores
originales. No ejecutado ni prueba de permisos. Las fuentes de los otros grupos
ya adquiridas no son servicios disponibles. Protoc69923 terminó; los esquemas originales ya están generados/compilados.
Usarlos al cerrar el build de libinit, sin volver a construir el generador.

[Metadatos nativos ejecutados](../reports/android16-native-property-libraries/validation.json):
ambos módulos completos, CRT y linker originales; generación y lectura sin
capacidades y con identidad 10000 real. Nativo y host difieren en 115 bytes por
orden de prefijos empatados; árbol completo equivalente y 4.145 consultas iguales,
sin modificar artefactos ni debilitar el control de propietario. Los archivos
estáticos y el wrapper no equivalen a PropertyInit o a un servidor de propiedades.

[Flags originales](../reports/android16-original-generators/validation.json):
generador fijado por Git blob, declaraciones y cadena fuente BP4A; dos módulos
compilados, sin constantes propias. Paridad de configuración con GSI no probada;
no inferir valores de paquetes ausentes del inventario system. Símbolos privados
de init localizados en minidebug y región leída mediante REA MCP/GDB, sin arrancar
init y con debugger cerrado. Protoc69923 ya terminó; consultar el checkpoint
vigente para procesos actuales, sin asumir actividad por sus PIDs históricos.

app_process original termina 0 sin readiness: fuente y diagnóstico muestran
retorno temprano de startVm por ro.product.cpu.abilist64 ausente, antes de crear
la VM. El snapshot de 101 sólo aplica system/build.prop, mientras existen 21 valores
system_ext y 58 product, además de los derivados por init.
[Pruebas](../reports/android16-framework-entry/validation.json).
El logger es instrumentación opcional mediante API original liblog: no una API
sustituta ni un preload de producción. /probe fue denegado por el namespace;
la captura en /data conserva sus restricciones.

El requisito libdexfiled.so está declarado sin condición en el JSON original.
De 41 requisitos system es el único sin proveedor declarado en este artefacto.
La fuente explica la discrepancia, pero la biblioteca sigue ausente y el estricto
global sigue fallido. No se ha añadido un sustituto ni editado el requisito.

Markor permanece intacto y sólo estuvo en CLASSPATH: no instalado, cargado o
ejecutado de forma demostrada. La invocación directa no zygote de ActivityThread
es exploratoria, no la ruta normal de lanzamiento APK. Seguir el ciclo original
de paquetes/zygote/AMS exige Binder, identidad/política y grupos de servicios;
todavía sólo se ha estudiado en fuentes. La matriz conserva nueve etapas no
probadas. R1 y el objetivo global siguen abiertos; sin reinicios ni Android boot.

## Historial conservado · no es el estado vigente


### Capa de compatibilidad APK propia sobre Linux

La dirección solicitada es estudiar AOSP para reutilizar o reproducir el mínimo
necesario para ejecutar APK de forma estable en Linux, sin Waydroid y sin arrancar
un sistema Android completo. Nuestro compositor y shell siguen siendo Rust/Smithay.
El desarrollo se organiza en [ROADMAP-A.md](ROADMAP-A.md).

## Qué se debe demostrar

Una APK propia, sin reescribirla como aplicación Linux, debe ejecutar su código,
resolver las APIs que usa, abrir una ventana en nuestro compositor, recibir entrada,
conservar estado y cerrar correctamente. Después se ampliará la compatibilidad
con APK reales y se medirán estabilidad, aislamiento y consumo.

Se investigarán por separado:

- DEX: ejecución y biblioteca de clases, estudiando ART/libcore y su posible uso host.
- Framework: subconjunto requerido de ciclo de vida, recursos, vistas y servicios.
- Gráficos/entrada: puente a Wayland y nuestra sesión Rust, con presentación real.
- JNI: ABI, bibliotecas nativas y compatibilidad Bionic cuando las APK lo requieran.
- Servicios: audio, red, almacenamiento y permisos incorporados según pruebas.

No se presupone que ART solo ejecute cualquier APK. La
[documentación de ART](https://source.android.com/docs/core/runtime) identifica
DEX como su formato de ejecución; la resolución de APIs y dependencias de la
aplicación constituye trabajo adicional de nuestra capa. Compartir el kernel
no convierte bibliotecas ARM en x86_64 ni garantiza compatibilidad de JNI.

## Primer estudio implementado

```bash
python tools/apk/apk_inventory.py ARCHIVO.apk INFORME.json
```

El analizador no instala ni ejecuta Android. Lee tablas DEX de versiones 035–040,
resta clases definidas en todos los DEX y registra referencias externas de plataforma,
propietarios de referencias de métodos y bibliotecas lib/ABI/*.so. Usa límites de
entrada y comprueba rangos básicos. El formato se basa en la
[especificación DEX](https://source.android.com/docs/core/runtime/dex-format).

El ensayo sobre VLC 3.7.1 x86_64 encuentra seis DEX, 1628 descriptores externos de
plataforma y cuatro bibliotecas nativas. Es una aplicación compleja de referencia,
no la APK elegida para el mínimo inicial. Ver reports/a0-apk-study/vlc-static.json.
Las referencias estáticas no indican qué código se ejecutará ni cubren reflexión,
JNI o carga dinámica. El informe no verifica firma, manifiesto, recursos o ELF,
no es un verificador DEX completo y no prueba compatibilidad ni ejecución.

## Alcance y recursos

No se iniciará una descarga del árbol AOSP completo por defecto. La cifra oficial
de 400 GB/64 GB corresponde al desarrollo de la plataforma completa y no se toma
como requisito demostrado de esta investigación selectiva. Los recursos de los
componentes elegidos deberán medirse. La VM dispone de unos 7,7 GiB y mantiene
un problema de estabilidad documentado en INCIDENTE-VM-20261030.md.

El contrato y adaptador Waydroid anteriores no se presentan como esta capa.
Se conserva el trabajo publicado como referencia histórica; su ampliación se ha
detenido. La aceptación de A no exige boot Android ni sys.boot_completed.

## APK propia preparada

La fixture fixtures/apk/counter ya está compilada y dispone de manifiesto, recursos,
fuentes y hashes. Su Activity contiene texto, botón y contador en preferencias.
No incorpora clases de framework Android ni bibliotecas JNI en el paquete.
La construcción no usó Android ni Waydroid. La ejecución DEX sobre Linux y el
puente de UI siguen pendientes. Ver reports/a0-fixture/ y el README de la fixture.

## ART host ejecuta DEX en Linux

Se descargó y verificó el conjunto ART 13 host publicado por R8, fijando revisión,
SHA-1 oficial y SHA-256. No se construyó ni arrancó Android. Una prueba DEX propia
pasó aritmética, recursión, interfaz, arrays, excepciones y reflexión básica en ART
con -Xint. La APK original del contador se encuentra en el classpath; su
MainActivity falla al resolver android.app.Activity, confirmado por el registro
de clases. No se ha ejecutado su ciclo de vida ni mostrado su interfaz.

El lanzador informa que falta framework/core.art y continúa sin imagen de clases
precompilada; la prueba semántica termina con código 0. La selección mínima,
compilación reproducible de ART y mediciones de consumo siguen pendientes. El
archivo del laboratorio no es el runtime final distribuible.
Ver ESTUDIO-ART-HOST.md y reports/a1-art-host/. A1/A2 no se dan por terminados.

## La APK propia ejecuta sus callbacks en Linux

El primer subconjunto de runtime/apk resuelve Activity, Context, View y preferencias
enteras. ART ejecuta el DEX de la APK original fijada: crea su árbol de texto/botón,
activa el listener 0→1→2 y, en otro proceso, recupera 2 y pasa a 3. No se recompilan
sus fuentes ni se incluyen clases org.archtv.probe en el DEX anfitrión. Los recursos
se leen de resources.arsc; una variante separada con DEX idéntico demuestra que el
texto cambia al cambiar el recurso.

El comprobador también verifica exclusión de un segundo proceso sobre datos
ocupados, liberación al cerrar, modos 0700/0600 y rechazo de recursos truncados y
preferencias corruptas. No hay ventana ni eventos Wayland todavía: A0/A1 están
verificados para esta fixture; A2 sigue en curso. La implementación no es una
capa Android completa ni aporta aún aislamiento o estabilidad prolongada.
Ver runtime/apk/README.md, CONTRATO-APK.md y reports/a1-counter-headless/.

## La APK tiene ventana Wayland y entrada real de la pila Linux

archtv-apk-host representa en Rust el árbol generado por la APK en ART. Dos
sesiones DRM/Pixman a 1280×720 verificaron Enter/Espacio desde uinput, 0→1→2,
cierre con Escape y reapertura persistente 2→3. Las capturas DRM y del cliente
coinciden exactamente en RGB. Los procesos y sesiones se cerraron y volvió tty1.
Ver APK-WAYLAND.md y reports/a2-wayland/. A2 está verificado para la fixture,
sin acreditar otras APK, mando físico, seguridad o estabilidad prolongada.

La siguiente dirección solicitada es portar componentes originales del framework
AOSP, adaptando dependencias a Linux. Las clases android.* actuales son propias;
la prueba existente será regresión durante ese port, no su resultado final.

## Compilación y primer enlace del framework original

Las fuentes originales fijadas de Looper, Handler, Message y MessageQueue compilan
sin cambios y se convierten a DEX. La referencia completa de API internas y las
dos declaraciones auxiliares son sólo de compilación y no están en ese DEX.
ART ejecuta Looper.prepare hasta el constructor original de MessageQueue, que
falla en nativeInit por ausencia de JNI. FileDescriptor.getInt$ se verificó en
el ART real. Aún no hay cola funcional ni sustitución de las API del contador.
Ver runtime/aosp/README.md y reports/aosp-queue-compile/.

## Puente JNI Rust de MessageQueue probado

Los seis métodos JNI se enlazan con epoll/eventfd. Pasan cuatro pruebas Rust con
FD reales y una prueba ART de creación, espera, despertar entre hilos, listener
Java público sobre una tubería y destrucción. SparseArray y tres utilidades se
compilan desde fuentes AOSP sin cambios, junto con las cuatro clases de la cola.
HandlerDispatchProbe aún falla por Parcelable ausente: no se acredita despacho
Java ni integración del framework original con la APK. Ver AOSP-JNI-LINUX.md y
reports/aosp-queue-jni/.

## Despacho Handler/Looper original verificado en Linux local

Se compilan 19 fuentes originales sin cambios. El adaptador Rust añade relojes
Linux, identidad local y lectura de propiedades del anfitrión. Handler.post y
Looper.loop pasan un Runnable y pruebas de orden, cancelación, diferidos, idle,
hilos cruzados, WorkSource, barreras, quit y quitSafely; la cola se repitió en diez
procesos ART. Binder IPC y el servicio global de propiedades no están implementados.
Un primer timeout quedó sin diagnóstico; se conserva ese límite en el informe y
no se considera resuelta la estabilidad. La APK aún usa el runtime anterior.
Ver AOSP-HANDLER-LINUX.md y reports/aosp-handler-foundations/.

## El principal original está integrado en la APK

El contador original ya crea y modifica sus vistas mediante mensajes de Handler
en el Looper principal AOSP, con comprobación de getMainLooper y del hilo main.
Pasan persistencia, 64 activaciones sin pérdidas, EOF, fallo de comando y reapertura.
La regresión DRM/Pixman 720p con uinput pasa y los frames coinciden exactamente
con las capturas DRM. Waydroid siguió inactivo y se liberaron sesión/procesos.
Ver APK-LOOPER-AOSP.md y los informes aosp-ui-headless y aosp-main-ui-wayland.
Activity/View/Bundle/recursos y preferencias siguen siendo propios; aún falta el
redibujado por cambios asíncronos y el resto del port, seguridad y estabilidad.

## Unidad nativa libinit · evidencia parcial vigente

[Validación](../reports/android16-libinit-native-unit/validation.json): las 52 fuentes
originales compilan con clang21/Bionic y perfil global original. 51 objetos se
reutilizan tras igualdad real del preprocesado y comprobación SHA; init.cpp se
compila al añadir el include exportado original de libxml2. Archivo prototipo de
63 miembros: 52 fuentes, tres protobuf, dos XSD y seis libcap. No equivale a Soong
completo: sanitización/configuración de producto y alineación de flags de los
protobuf siguen abiertas, junto al enlace y ejecución supervisada de PropertyInit.

XSDC original genera el esquema APEX; sus dos fuentes C++ compilan para Bionic.
Rust1.88 original usa su std Android x86_64, sin objetos glibc en target. La FFI
original genfslabelsversion se enlaza y ejecuta en cuatro casos reales: ausente,
válido, malformado y permiso denegado. UID10000, sin grupos/capacidades, NNP1.
El fallback original 202404 no demuestra mediación SELinux. No servidor, boot
Android, aplicación ni etapa de la matriz aceptados por estas pruebas.


## Decisiones offline con herramientas originales

[Evidencias](../reports/android16-policy-semantic-baselines/validation.json): diez
consultas de inventario y catorce consultas de acceso mediante libsepol original:
seis permisos concedidos, tres denegaciones y cinco errores de contexto/clase/permiso.
Los errores no se contabilizan como denegaciones. Un permiso por invocación evita
el límite identificado en el bucle original de argumentos. No hay enforcement
vivo, política compuesta ni aceptación de aplicaciones.

Se descarta usar sepolicy-check como oráculo general: no representa todas las
condiciones efectivas y su máscara de permisos es limitada. seamendc tampoco es
un compositor completo: omite construcciones y nunca debe sustituir las aserciones
neverallow originales. La siguiente unidad debe conservar las fuentes completas,
resolver clases, atributos, usuarios/roles y MLS explícitamente y contrastar
semántica global; catorce casos no demuestran equivalencia. Ninguna base elegida.

## Control experimental de namespaces de política

[Resultados](../reports/android16-policy-namespace-controls/validation.json): el
compilador original rechaza sensibilidad/categorías dentro de bloques. Mover sólo
esas declaraciones al nivel global permite compilar AOSP (salida0 en29,8s tras
un primer límite de25s). Nueve consultas seleccionadas conservan su resultado
con nombres prefijados; no acreditan equivalencia completa. La clase original
service_manager deja de existir y aosp.service_manager no conserva su contrato
de nombre. Usuarios/roles/tipos/contextos también cambian. No es una política
de despliegue ni composición Linux/AOSP aprobada. Siguiente: preservar contratos
Android de clases/contextos y resolver explícitamente los globales MLS/SID y
la integración Linux, conservando todas las aserciones. Nada cargado o reiniciado.

## Integración de política · namespace Linux y conflicto de SID

[Ensayos](../reports/android16-linux-policy-namespace/validation.json): refpolicy
completa compila en namespace Linux con clases/common/MLS y nombres SID globales.
Cinco consultas seleccionadas con clases originales mantienen sus resultados;
no prueban equivalencia completa ni etiquetas/transiciones del host. Una unión
explícita propuesta contiene145 clases y como máximo32 permisos por clase.

El control de composición conserva reglas/aserciones de ambas fuentes, mantiene
nombres Android y separa símbolos Linux; el compilador original lo rechaza
porque un SID inicial no puede tener dos contextos. Hay27 contextos iniciales
literalmente distintos entre las fuentes. La siguiente decisión debe justificar
qué contexto global representa cada SID y cómo conservar la mediación Android
y Linux, junto a restricciones MLS y accesos entre dominios. No eliminar
contextos/asserts para aceptar una compilación. Ninguna política elegida, cargada
o validada con servicios/APK; no se reinició la VM.

## Resultado más reciente de integración de política

[SID/etiquetas](../reports/android16-policy-sid-ownership/validation.json): ambas
hipótesis de SID fallan255 en genfscon;29 coincidencias literales de etiqueta.
Siguiente: integración explícita del etiquetado Linux/AOSP; ninguna base elegida.
[Decisión y límites](ARQUITECTURA.md#sid-y-pseudoarchivos-conflicto-de-etiquetado-compartido).

## Resultado vigente: universos de tipos

[Composición actual](../reports/android16-policy-global-labels/validation.json):
el compilador emitió fallos neverallow antes del límite90s. not/all incluye
tipos ajenos pese a namespaces. Siguiente: delimitar universos preservando
proyecciones originales y comprobar mediación; no omitir aserciones.

## Último resultado: compilación con universos explícitos

[Compilación0 y comparaciones](../reports/android16-policy-type-universe/validation.json):
439 atributos conservados coinciden con sus controles y nueve decisiones válidas
se mantienen.100 atributos Linux faltaban ya en el control aislado; semántica
completa pendiente. La app Android no puede buscar la raíz proc con etiqueta
Linux. Siguiente: mediación precisa de etiquetas y revisión de proyecciones;
ningún servicio/APK aceptado ni política cargada.

## Último resultado: adaptador proc offline

[Compilación/comparación](../reports/android16-policy-proc-adapter/validation.json):
se recuperan ocho permisos de directorio; seis denegaciones y nueve casos
originales se conservan. La exportación completa añade sólo la regla prevista.
Pendiente: contratos SELinux del gestor, tres denegaciones modeladas y pruebas
reales. Ningún host/servicio/APK aceptado; no se cargó la política.

## Último resultado: consultas SELinux del gestor offline

[Resultados](../reports/android16-policy-manager-selinux/validation.json): tres
reglas recuperan consultas de estado/access en el modelo;28 controles nuevos,
17 previos y9 originales concuerdan. Administración sigue denegada. Delta
exportado de3 reglas, sin cambios de atributos. Siguiente: clausura real de
contexto/etiquetas/montajes/Binder del gestor; ningún endpoint/servicio/APK
ejecutado o aprobado por estas pruebas, ni política cargada.

## Último avance: constructor reproducible del artefacto

[Herramienta y controles](../reports/android16-policy-builder/validation.json):
genera/compila el mismo candidato sin scripts temporales; binario idéntico,
deriva/sobrescritura rechazadas y cancelación acotada comprobada.
[Comando y requisitos](ARQUITECTURA.md#artefacto-reproducible-de-política-experimental).
No instala/carga política ni acepta servicios/APK. La activación real del host
sigue pendiente bajo el contrato sin reinicio ni introducción de VM.

## Último avance: contrato kernel upstream

[96 clases/1694 permisos](../reports/android16-kernel-policy-contract/validation.json)
cubiertos por el candidato;11 SID activos con numeración coincidente. El
constructor verifica el contrato fijado y produce el mismo binario. No es
prueba del kernel del paquete, de mapeo activo ni de servicios/APK. Próximo:
clausura real de contexto/identidad/montajes/Binder y trabajo independiente,
conservando la prohibición de introducir VM o reiniciar.

## Binder original: nuevo resultado parcial

[13 regresiones nativas originales pasan](../reports/android16-binder-kernel-contract/validation.json); cinco casos de gestor excluidos. SID real obligatorio en transacciones entrantes; identidad/gestor/SELinux/APK aún no aceptados.

## Contraste SID del driver

[Resultado nativo](../reports/android16-binder-secctx-probe/validation.json): transacción síncrona sin SID con PID/UID correctos; solicitando SID fallaba BR_FAILED_REPLY, error extendido -95/EOPNOTSUPP en el arranque previo sin LSM activo; la sonda posterior al reinicio descrita arriba supera ese transporte. Sonda propia, sin aceptación de gestor/MAC/APK ni cambios al host.

## R3: SurfaceFlinger original estudiado

[Contrato gráfico](../reports/android16-surfaceflinger-contract/validation.json): Composer real y hotplug inicial obligatorios por fuentes;48 dependencias directas presentes sólo estáticamente. Ningún SF/HAL/puente ejecutado. R1-MAC conserva el fallo SID probado.

## R3: rutas de reutilización

[Comparación de fuentes](../reports/android16-composer-reuse/validation.json): A16 conserva HWC2On1; HAL Wayland1.5 tiene acoplamiento a interfaces propias y sync por demostrar. Composer DRM AIDL del manifiesto requiere KMS master. Probar adaptación/reutilización antes de Composer propio; sin ejecución gráfica aceptada.

## R3: HWC2On1 original construido y cargado

[Enlace y carga Bionic](../reports/android16-hwc2on1-build/validation.json): dos unidades originales completas sin modificar, enlace estricto y dlopen NOW/dlclose0 reales mediante REA MCP con UID10000 sin capacidades. Namespace plataforma probado; vendor/HIDL/dispositivo/sync/frames/APK sin probar.

## R3: fallo inicial de carga vendor · histórico

[Prueba sphal real](../reports/android16-hwc-vendor-load/validation.json): namespace visible, carga original falla por libutils.so no disponible allí. El dlopen de plataforma anterior no acreditaba esa frontera. Construir variantes vendor originales; sin fallback ni namespaces relajados.

## R3: conjunto vendor original carga en sphal

[69 fuentes originales y carga nativa](../reports/android16-vendor-libutils/validation.json): cinco bibliotecas enlazadas estrictamente más libc++ prebuilt elegido por AOSP. Carga/descarga originales0 y seis paths vendor mapeados mediante REA MCP, namespace intacto. Es un perfil experimental, sin equivalencia Soong/ABI completa ni HAL, buffers/fences, frames o APK aceptados.

## R3: herramienta HIDL y transporte generado

[Generación original](../reports/android16-hidl-generator/validation.json): herramienta host66 unidades enlaza, nueve hashes .hal congelados y SHA256 independiente coinciden;39 fuentes/cabeceras generadas. MCP observa cuatro hashes Composer. Hash de archivo no certifica parser/ABI; bindings nativos/servicio/HWC/frames/APK pendientes. Fuente opcional loader parcial por HTTP429, preservada.

## R3: bindings Bionic y cargador original

[Resultado parcial](../reports/android16-hidl-native-bindings/validation.json):14 unidades generadas nativas, servicio/HwcLoader y adaptador framebuffer compilan. ComposerResources queda detenido por cabeceras libui ausentes. Fuente parcial recuperada sin descartar archivos; agrupación libhidlbase/hwbinder conservada. Sin enlace, servicio activo, dispositivo, frame o APK; chequeo host sigue sin SELinux.
