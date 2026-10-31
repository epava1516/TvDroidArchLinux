# Roadmap A · plataforma APK general sobre Linux

Estado vigente: prefijo MC1 original probado en enforcing acotado, con negativo
de bypass y cierre real; anfitrión devuelto automáticamente a permisivo. El hito de firma Markor usa apksig
original y negativo de manipulación. No hay APK instalada ni aplicación lanzada.
El usuario autoriza operaciones necesarias en esta VM; la corrección y recuperación
se verifican por candidato, sin nuevas esperas por permisos históricos.

## Prioridad vigente · A16-QPR2-1

Aplica el [contrato actualizado](CONTRATO-APK.md). Android16 QPR2, Bionic nativo y
primera hipótesis SurfaceFlinger→Wayland reemplazan la selección A/B/C y API33
anteriores. La base nueva se mantiene aislada; no se descartan el compositor,
instalación, herramientas o regresiones útiles. Reinicios necesarios autorizados expresamente; checkpoint y recuperación antes de interrupciones.

## Camino crítico vigente · Markor completo

[Decisión y ejecución actual](../reports/android16-markor-critical-path/findings.json).
El hito auxiliar en curso quedó guardado aparte en311c25f. No ampliar herramientas
ni fixtures como prioridad: cada experimento debe desbloquear una fila de esta
secuencia y conducir a integración o a una decisión explícita.

[Hito funcional actual](../reports/android16-mc1-functional-candidate/findings.json):
MC1 recorre propiedades originales → servicemanager registrado → cliente original
lista `android.os.IServiceManager`, con cierre real0, en **permisivo con política**.
Entrada Linux/glibc→Bionic y NNP1 reales; imágenes originales RO conservan etiquetas.
No es autorización/aislamiento ni APK compatible. Antiguos bloqueos sin política
superados para esta cohorte; avisos de recursos conservados. Autorización expresa
actual cubre pruebas de seguridad/reinicio; no falta permiso. Antes de enforcing,
mantener recuperación y verificar los negativos de cada nueva cohorte. El prefijo
actual ya pasa con rollback probado; siguiente hwservicemanager/Composer y display
real intercalado con MC2 original, no más sondas ajenas a ese camino. ARM/GMS/DRM continúan separados.

| Paso | Integración y resultado funcional exigido | Estado/evidencia y límite |
| --- | --- | --- |
| MC0 · admisión MAC recuperable | Candidato coherente de política original Linux/AOSP, imágenes/etiquetas/UID/roles/NNP/capacidades, dispositivos/cgroups/FD y recuperación; prueba real y recuperación antes de cada operación disruptiva | Política compuesta cargada; entrada real Linux/glibc→Bionic y propiedades ya ejecutan en enforcing en ventana acotada. Autorización actual expresa; recuperación automática probada. R1-MAC sigue abierto: recorrido completo enforcing y negativos pendientes |
| MC1 · cohorte original disponible | Propiedades originales publican versión y readiness por sus controles reales; servicemanager se registra y cliente original legítimo lo consulta; después hwservicemanager para la ruta Composer elegida. Identidad/SID y negativos reales, muerte/cierre sin alterar host | Propiedades→gestor registrado→cliente original→cierre0 probado en permisivo con identidades y etiquetas reales. El mismo prefijo pasa enforcing1, directo-helper denegado y cierre real, en ensayo4s recuperado0 (ejecución23). Hwservicemanager pendiente; R1-MAC no cerrado. No readiness manual ni APK disponible |
| MC2 · instalación y lanzamiento reales | Reutilizar PackageManager/permisos/instalación/datos, AMS/ATMS y proceso ART/zygote/framework originales como subsistemas. Resolver cierre real de system_server y auxiliares (p.ej. installd/artd/almacenamiento) por fuentes/ejecución; instalar APK Markor intacta y lanzar Activity/Application originales | ART llega a ActivityThread.main; no lanzamiento Markor. Lista mínima exacta y separación de system_server aún por demostrar; no asumir que todas sus dependencias puedan omitirse. Firma criptográfica v2 API36 verificada con apksig original y negativo; splits/UID/seinfo/datos siguen pendientes. SystemServer original espera display antes de PMS: intercalar MC3, no asumir instalación headless |
| MC3 · interfaz e entrada | Completar Composer/allocator/mapper→SF original→Wayland/Smithay, WMS/Display/Input originales; presentar frames de Markor y entregar entrada al editor/foco | Composer espera gestor; no buffers/fences ni frame original acreditados. Reutilizar subsistemas completos; no reconstruir widgets de Markor. Empaquetado de cierre gráfico exacto pendiente, no bloqueo atribuido sin prueba |
| MC4 · función, persistencia y servicios | Crear/editar nota con entrada real, guardar por la ruta/proveedor elegido y permisos originales; verificar bytes, callbacks y almacenamiento efectivo | No probado. Proveedores/actividades de selección y auxiliares que exija el recorrido se integran, no respuestas vacías ni ruta cambiada silenciosamente |
| MC5 · cierre y reapertura | Cerrar desde shell, recoger procesos/recursos, reabrir APK intacta y recuperar nota; repetir con límites/aislamiento y control horizontal Calculator | Nueve etapas canónicas siguen no probadas. Pruebas del supervisor sólo respaldan infraestructura de ciclo de vida |

La propuesta concreta de MC0/MC1 y sus condiciones de prueba/recuperación están
en [arquitectura](ARQUITECTURA.md#integración-inmediata-de-propiedades-y-gestores).
El arranque histórico por sí solo no autorizaba cambios; la autorización expresa actual sí cubre carga, etiquetas, enforcing y reinicios necesarios. ARM, GMS,
multimedia propietaria/DRM siguen en R5–R7 y la matriz amplia, fuera de este primer
camino Markor. La secuencia completa no se cierra con MC1 ni con una ventana vacía.

## Puertas de seguridad y antecedentes

Vigente: autorización expresa actual cubre carga, etiquetas, enforcing y reinicios.
Política cargada y ventanas recuperables ejecutadas, no sólo preparación offline.
R1-MAC permanece abierto: las pruebas de la cohorte no acreditan aislamiento de
APK ni operación estable del anfitrión en enforcing sostenido. El plan S0–S5 de
[arquitectura](ARQUITECTURA.md#plan-de-seguridad-y-recuperación-del-anfitrión)
se aplica con resultados reales del [checkpoint actual](../reports/android16-mc1-functional-candidate/checkpoint.json).

| Puerta | Dependencias y trabajo | Evidencia de salida | Estado |
| --- | --- | --- | --- |
| R0 · procedencia | Verificar versión/rama/tag/build, resolver todos los repositorios, elegir target y artefactos coherentes; revisar licencias y mantenimiento | Manifiesto con revisiones exactas/procedencia, hashes de binarios y configuración; separación referencia vs parches de seguridad | Tag/rama/build y manifiesto de 1.013 commits fijados/reproducidos; diez objetos principales contrastados. GSI x86_64 coincidente y preparación de 36 APEX/4.395 archivos reproducida. Configuración parcial ejecutada; equivalencia fuente/binario completa, licencias y seguridad pendientes |
| R1 · runtime Bionic coherente | R0; Bionic/linker/ART/libcore/APEX/framework/JNI/recursos y configuración original; bootclasspath/classloaders/namespaces/propiedades y kernel | Ejecución reproducible del motor, cierre de dependencias/configuración/identidad y fallos honestos; no mezclar Android13/host sin frontera probada | Parcial A16: ART alcanza ActivityThread.main sin Markor; BCP46 y170 propiedades originales comprobados. Servicio de propiedades original tiene carga persistente, rechazo por socket y [adaptaciones de errores/cierre/acciones](../reports/android16-property-actions/findings.json) con ejecuciones MCP acotadas. Coordinador reutiliza ActionManager/eventfd, no SecondStageMain; comandos de regresión no acreditan APK. [Supervisión Rust↔Bionic](../reports/android16-rust-supervisor/findings.json) ejecutada en diagnóstico con cierre cooperativo/pidfd; normal sin SELinux se rechaza. Backend Linux de servicios/ctl/power, operaciones autorizadas/MAC, integración compositor/restart/watchdog, durabilidad general, cierre global libdexfiled.so y equivalencia Soong/GSI pendientes. [Historial y alcance por resultado](EVIDENCIAS.md). |
| R1-MAC · política Linux e IPC original | R0/R1; SELinux activo, política/etiquetas/transiciones compatibles con Linux anfitrión, Binder/HIDL/vendor privados y gestores originales, propiedades/VINTF | Registro y descubrimiento reales, identidad/denegación/callbacks/muerte; host funcional y apps separadas; instalación/activación/rollback de política probados | Política compuesta cargada; original Linux→Bionic/propiedades/gestor/cliente/cierre probados en permisivo y progresión enforcing con rollback automático. Evidencia vigente en android16-mc1-functional-candidate. Puerta ABI/kernel/seguridad de APK, negativos completos y anfitrión enforcing sostenido permanecen abiertos; permisos históricos no bloquean pruebas autorizadas |
| R2 · comportamiento y servicios | R1; evaluar unidades originales completas de paquetes/permisos/Activity/Binder/Content/servicios/segundo plano; conservar agrupaciones grandes si conviene | Semántica real, callbacks/concurrencia/error/persistencia/muerte/IPC y separación por app; cierre transitivo. Conflicto con Android completo documentado antes de cambiar alcance | Entrada parcial original RuntimeInit/ActivityThread.main alcanzada (R1); [Cuatro perfiles de servicio originales parseados](../reports/android16-service-profile/findings.json) en rutas canónicas, con negativos de configuración; sin activar servicios. Backend debe rechazar listas parciales, inicializar SIGCHLD antes de hilos y preservar contextos/identidad/cgroups/reaper/fallos. Paquetes/permisos/lifecycle/Content/servicios aún sin recorridos reales verificados. No asumir separación fácil de system_server ni usar main directo como lanzamiento APK |
| R3 · salida gráfica y entrada | R1/R2; contrastar primero SF original, WM/Surface/BufferQueue/HWC/RenderEngine y puente Wayland hacia Smithay | Buffers/fences/ownership, aceleración/composición/ventanas/escalado/foco; teclado/ratón/táctil/mando; multimedia con superficie y sync AV | [Contrato fuente/ELF estudiado](../reports/android16-surfaceflinger-contract/validation.json): Composer AIDL o HIDL real y hotplug inicial necesarios;48 dependencias directas con candidatos, cierre GPU/allocator/mapper pendiente. [Reutilización estudiada](../reports/android16-composer-reuse/validation.json): HWC2On1 sigue en A16; HAL Wayland con dependencias propias/sync, HWC3 DRM con KMS master. [HWC2On1 original compila/enlaza y carga Bionic](../reports/android16-hwc2on1-build/validation.json); [conjunto vendor original carga en sphal](../reports/android16-vendor-libutils/validation.json):69 fuentes, cinco bibliotecas y libc++ prebuilt AOSP, seis paths vendor mapeados. Perfil experimental sin equivalencia Soong/ABI completa; [hidl-gen host66 unidades,9 hashes y39 archivos generados](../reports/android16-hidl-generator/validation.json), [14 objetos Bionic y servicio/HwcLoader compilan](../reports/android16-hidl-native-bindings/validation.json), fallo inicial de recursos por libui conservado. [Entradas originales libui y codecs](../reports/android16-libui-source-closure/validation.json): AIDL fuente SDK36,31 IDL/124 archivos,32 objetos incluido ComposerResources; dos codecs enlazan y regresión AParcel local FD/metadata termina0 mediante REA MCP. No transferencia Binder. [23 unidades originales libui/libui-types compilan](../reports/android16-libui-implementation/findings.json) tras generar allocator/mapper y suministrar exports originales; [Enlace estricto libui y ejecución nativa de geometría/sentinel](../reports/android16-libui-link/findings.json) pasan tras aplicar -fno-rtti original a23 unidades y dos dependencias estáticas. Sin equivalencia Soong completa ni allocator/mapper/buffers/fence real/Composer aceptados. Agrupación original libhidlbase/hwbinder identificada; enlace/HIDL funcional/dispositivo/sync pendientes. Adaptar candidatos antes de Composer nuevo. [Servicio Composer2.1, recursos y framebuffer enlazan](../reports/android16-composer-link/findings.json); arranque MCP queda esperando hwservicemanager.ready hasta límite/señal9, sin carga HAL acreditada. Prioridad gestores reales/R1-MAC, no readiness ficticia. Hipótesis SF→Wayland no ejecutada; R1-MAC sigue requerido. No sustituir por widgets propios |
| R4 · vertical Markor | R0–R3 e instalación/firmas/datos; APK intacta y recorrido de nota ya definido | Instalar→lanzar→UI original→entrada/editar→guardar/proveedor elegido→servicios→cerrar→reabrir; bytes/eventos/frames y fallos trazables | Nueve etapas no probadas sobre A16 |
| R5 · horizontal y TV | R4 como primera referencia, sin excluir análisis temprano de riesgos; Calculator/JNI, VLC/AV, Android TV, WebView/aceleración/externos y APK por API/ABI | Misma base en categorías distintas sin reconstrucciones por APK; matriz por versión/función, nueve etapas y tres ejes. Casos posteriores a API base y apps OEM/privilegiadas explícitos | Pendiente; artefactos adicionales por fijar |
| R6 · ISA y 32/64 | Fronteras de R1; [investigación separada](TRADUCCION-ARM.md): Native Bridge original, libndk_translation, Houdini, candidatos abiertos; QEMU user-mode aparte | Artefacto/licencia/derechos, guest closure/JNI/zygote y recorridos reales por combinación; no motor propio sin insuficiencia demostrada de opciones existentes | Interfaz A16 y ELF original estudiados; fuentes/metadatos y licencias revisados. Proveedores/ARM32/64 y APK ARM no probados; sin cambios al runtime x86_64 |
| R7 · conformidad técnica y producto | R1–R6, H7–H9; CDD16/CTS16.1 pertinentes, seguridad, medidas y paquete/instalación/actualización | Tests ejecutados y no ejecutados, sin afirmar certificación; presupuestos por hardware, estabilidad/recuperación, UID/permisos efectivos, splits/firma/ABI/migración/desinstalación/rollback/licencias/parches | Pendiente |

La primera secuencia es R0→R1, después Markor con R2/R3 y validación horizontal.
Una fixture semántica o un frame no cierran R1 completo ni R4/R5. Se preserva
compatibilidad amplia con aplicaciones arbitrarias como meta, sin prometer
universalidad ni seleccionar sólo casos fáciles. Un límite necesita evidencia,
clasificación y plan explícito, no un porcentaje inferido de casos no probados.

Para cada decisión: alternativa elegida, motivo, evidencia, cambio propio,
dependencia y aceptación. Seguir las siete fases de diagnóstico del contrato;
corregir subsistema/frontera y probar beneficio para otra app. Las correcciones
particulares por APK y respuestas vacías no son estrategia.

Referencia técnica: [CDD16](https://source.android.com/docs/compatibility/16/android-16-cdd)
y [CTS oficial](https://source.android.com/docs/compatibility/cts/downloads), familia
16.1 para QPR2. Introducir módulos pertinentes de recursos, Binder/permisos,
paquetes/splits/lifecycle/graphics/media/TV según el entorno permita; fijar suite,
comando y revisión, guardar también tests no ejecutados y causas. Un subconjunto
no es certificación. Referencia Android externa cuando sea posible, sin arrancar
otro Android local sin autorización. GMS/microG/DRM/OEM/backends siguen con pruebas
y requisitos externos separados en la matriz; entender una interfaz no las cierra.

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

R1-MAC: las dos hipótesis de SID alcanzan conflicto genfscon (255), con29
coincidencias de etiquetas originales. Requiere tabla global justificada y
pruebas de mediación/transiciones; no omitir mapeos para compilar.
[Evidencia](../reports/android16-policy-sid-ownership/validation.json).

R1-MAC: [la composición de etiquetas](../reports/android16-policy-global-labels/validation.json)
alcanza fallos neverallow: el namespace no acota not/all. Exigir universos
explícitos y proyección semántica original antes de aprobar política.

R1-MAC: [universos explícitos](../reports/android16-policy-type-universe/validation.json)
compilan0 con aserciones;439 atributos retenidos y nueve decisiones válidas
coinciden con controles. Pendientes100 atributos eliminados en el control,
proyecciones completas y mediación: app Android→proc Linux denegado7.
No hay política de despliegue ni readiness de servicios/APK.

R1-MAC: [adaptador proc offline](../reports/android16-policy-proc-adapter/validation.json)
compila con aserciones; ocho permisos recuperados, seis denegaciones y nueve
casos originales conservados; delta binario exportado de una sola regla.
Siguiente: contratos SELinux del gestor y mediación por clase/permiso, junto
a pruebas reales de identidad, denegaciones y transición. No readiness/APK.

R1-MAC: [consultas SELinux del gestor](../reports/android16-policy-manager-selinux/validation.json)
compilan con aserciones y delta de3 reglas; administración sigue denegada en
el modelo. Exigir endpoints/contextos/montajes/Binder/denegaciones reales,
no convertir28+17+9 consultas offline en readiness ni compatibilidad APK.

## Historia · etapas anteriores, no prioridad vigente


# Roadmap anterior · laboratorio Android13

Objetivo aclarado por el usuario: estudiar AOSP y reproducir o reutilizar el mínimo
necesario para ejecutar APK de forma estable sobre Linux, dentro de nuestra sesión
Rust/Smithay. No se persigue arrancar un sistema Android completo ni envolver
Waydroid. El éxito se mide por ejecución real de aplicaciones, no por boot Android.

| Etapa | Trabajo concreto | Puerta de salida | Estado |
| --- | --- | --- | --- |
| A0 · superficie real | APK propia pequeña, inventario DEX/recursos/JNI y pruebas funcionales; revisar contrato según esas necesidades | APK y fuentes fijadas, APIs realmente usadas identificadas, pruebas reproducibles | Verificado para la fixture: inventario, recursos, firmas y comportamiento; contrato experimental en CONTRATO-APK.md |
| A1 · ejecución DEX | Estudiar ART/libcore en modo host y alternativas; prototipo de ejecución sobre Linux sin sistema Android | Código DEX de la APK ejecutado con salida verificable, sin Waydroid ni arranque Android | Verificado para la APK propia: ART ejecuta onCreate/onClick y conserva preferencias entre procesos; interfaz del prototipo verificada en A2 |
| A2 · primera interfaz | Subconjunto medido de Activity, ciclo de vida, recursos, View/texto/botón y entrada; puente hacia Wayland/Rust | APK propia sin modificar abre ventana, responde a entrada, guarda estado y se cierra correctamente | Verificado para la fixture: DRM/Pixman 720p, uinput→Wayland, cierre y reapertura 2→3; Activity/View propios; cola, contexto y recursos originales integrados |
| A3 · servicios mínimos | JNI/ABI/Bionic donde sean necesarios, gráficos, audio, red, archivos y permisos según APK de prueba | Pruebas por API/servicio, errores explícitos en funciones ausentes y recuperación | En curso: JNI Linux, Log y recursos/contexto originales verificados para fixtures; gráficos, audio, red, archivos y permisos pendientes |
| A4 · compatibilidad y estabilidad | APK reales por ABI/API, reflexión, WebView y demás dependencias descubiertas; ampliar la capa con evidencia | Matriz por aplicación, pruebas prolongadas, reinicios y mediciones; fallos y cobertura registrados | Pendiente |
| A5 · distribución | Runtime y servicio anfitrión propios, paquetes, actualizaciones, migración de datos e integración TV | Instalación limpia sin Waydroid ni sistema Android completo, apps verificadas, actualización y rollback | Pendiente |

## Puertas vigentes BASE-AOSP-1

Estas puertas preceden a más ampliaciones por métodos aislados. No sustituyen
A3–A5 ni H6–H9 y no convierten sus preparativos en compatibilidad.

| Puerta | Dependencias y experimento | Aceptación verificable | Estado |
| --- | --- | --- | --- |
| D0 · base oficial | Fuentes/targets x86_64, imagen/artefactos/versiones y licencias; distinguir Cuttlefish, Emulator y Android-x86 | Identidad completa y origen; implementaciones DEX/ELF frente a stubs; revisión de build soportada/patches antes de distribuir | Parcial: imagen oficial API33 r2 e inventario fijados; build reciente/distribución pendientes |
| D1 · cierre Bionic | D0; inventariar linker/libc/ART/libcore/APEX/JNI/recursos del mismo target, DT_NEEDED/configuración/classloader | Todas las entradas identificadas, ausencia/mezcla explícita; pruebas de loader y ART en namespace sin Android init ni VM/contenedor Android completo | Parcial: linker original --help/--list pasa; 46 bibliotecas inventariadas. ART target aborta por configuración original ausente en harness, antes de DEX |
| D2 · fronteras Linux | D1; IPC/FD/buffers/entrada, identidad/permisos, servicios originales individuales y recuperación | Contrato por proceso/biblioteca, cierre transitivo, operación/denegación/caída/cierre; sin ampliar a un boot Android oculto | Pendiente; registro Binder local no prueba IPC |
| D3 · aplicación original | D2; Markor intacta, manifiesto/alias, Package/Permission/Activity/Content, resources/JNI por subsistemas | Application/Activity/callbacks originales y dependencias reales identificadas; errores honestos | Host pendiente: XML leído, fallo IPermissionManager.getSplitPermissions; B sin probar. No código Markor ejecutado |
| D4 · vertical y elección | D3; misma APK/datos/entrada y condiciones para A y B; C sólo con frontera probada | Seis etapas Markor: ventana original→editar→guardar→servicio/proveedor elegido→cerrar→reabrir, bytes/eventos/frames/logs, aislamiento y costes. Decisión motivada; sin ganador por mera compilación | Todas las etapas funcionales siguen sin verificar |
| D5 · cobertura amplia/externa | D4 como primera referencia, sin bloquear análisis paralelo de riesgos; Calculator/VLC y APK GMS/DRM/ARM-only/splits/WebView reales | Pruebas por función, versión y ABI; comparar candidatos existentes; auth/backend/licencias/certificación/hardware y resultados negativos explícitos. Cada eje API/ABI/ISA independiente | Parcial estático; GMS/DRM comercial sin app/credenciales/contenido fijados; no cobertura acreditada |
| D6 · producto | D4/D5 y H7–H9; estabilidad, presupuestos y actualización de base coherente | Medidas globales incluyendo servicios, instalación limpia, migración/rollback y matriz repetible tras actualizar | Pendiente |

Experimento vertical: [CONTRATO-APK.md](CONTRATO-APK.md). Primer riesgo a reducir:
linker/ART Bionic originales como componentes Linux aislados; timeouts, credenciales,
procesos/handles, cierre y archivos expuestos deben registrarse. No se inicia Android
para obtener un resultado de referencia. Después se conecta la ruta original de
Markor a Smithay; las pruebas de fixture sólo guardan regresiones y no eligen base.

Para la comparación A, evaluar también ATL/art_standalone con revisión/licencias
fijadas y la misma Markor; sus demos, stubs o widgets GTK no son aceptación local.

Antes de escribir un nuevo servicio, investigar el subsistema original y su cierre,
consultar implementaciones existentes y asociarlo a una etapa real de la aplicación.
Si un servicio sólo puede reutilizarse dentro del boot completo, registrar conflicto
con el contrato y alternativas; no vaciar sus respuestas ni recortar la matriz.
Sin datos suficientes A/B/C quedan no decididas y se ejecuta la siguiente prueba
que discrimine el riesgo, manteniendo compatibilidad amplia como objetivo.


## Prioridad vigente

Ejecutar las puertas BASE-AOSP-1 después de la revisión de arquitectura.
Mantener la matriz de aplicaciones reales y sus dependencias externas, ABI e ISA. [ESTADO.md](ESTADO.md) es el punto de entrada; [EVIDENCIAS.md](EVIDENCIAS.md)
separa resultados publicados, experimentos pendientes y ensayos históricos.
A0–A2 de la tabla sólo acreditan fixtures; A3–A5 y compatibilidad amplia siguen
abiertos. El historial siguiente conserva los primeros experimentos y sus
fronteras sucesivas: una frase «siguiente paso» histórica no es la prioridad actual.

### Entregables actuales de la reconducción

- [Revisión de arquitectura y reutilización](ARQUITECTURA.md): conservar runtime y
  framework originales por conjuntos; no ampliar Activity/widgets propios para
  aparentar compatibilidad. Bionic/libhybris/servicios e ISA tienen decisiones y
  pruebas pendientes explícitas.
- [Matriz de APK reales](COMPATIBILIDAD-APK.md): Markor, Calculator y VLC con hashes
  y evidencia estática REA. Los seis pasos funcionales de cada app siguen not_run.
- Primer recorrido: Markor → nota local → edición → guardar → cerrar/reabrir.
  Antes: decisión de base mediante D0–D4, aislamiento/identidad, bootstrap original
  Application/Activity, presentación y entrada reales. No cerrar A3–A5 por el
  ensayo de enlace de clases del framework original.

## Primer experimento (histórico)

1. Crear una APK propia con una Activity, texto, botón y contador persistente,
   sin bibliotecas JNI ni dependencias adicionales en su primera versión.
2. Fijar sus fuentes, SDK, APK y hashes; analizar referencias y recursos.
3. Probar ejecución DEX fuera de Android. Evaluar reutilización selectiva de ART
   y libcore antes de escribir un runtime completo desde cero.
4. Implementar las APIs que esa APK requiere y un puente de ventana/entrada hacia
   el compositor; ninguna pantalla simulada cuenta como ejecución de la APK.
5. Verificar cierre, estado, repetición y consumo. Ampliar el conjunto de APK y
   APIs con resultados de ejecución, manteniendo la meta de estabilidad.

AOSP aporta especificaciones y componentes que se estudiarán individualmente.
Zygote, system_server, SystemUI, SurfaceFlinger, HAL y Binder no se convierten en
requisitos globales por defecto: cada dependencia deberá justificarse o adaptarse
según la ruta elegida y las aplicaciones. Tampoco se afirma que todos puedan
eliminarse conservando cualquier API; esa compatibilidad debe demostrarse.

## Corrección del enfoque anterior

Los tipos AndroidProvider y el adaptador de estado Waydroid publicados son trabajo
previo y una referencia del laboratorio. No son el entregable de este roadmap ni
un prerrequisito para A1. Se detuvo su ampliación; el inventario Waydroid no
publicado se archivó fuera del repositorio. El contrato mínimo se revisará a la
luz de los experimentos, sin exigir sys.boot_completed ni un arranque AOSP.

Las validaciones funcionales, de ligereza, estabilidad e instalación del proyecto
siguen vigentes. H6 contiene resultados del laboratorio Waydroid; no se reutilizan
como prueba de la futura capa. La infraestructura para compilar una plataforma
AOSP completa no se presupone necesaria para investigar este runtime mínimo.

## Fixture disponible

fixtures/apk/counter contiene fuentes, recursos, manifiesto y APK de prueba
propia. Compila con AAPT2/D8 y clases API 28 fijadas por hash, sin arrancar Android.
Dos builds sin firma resultaron idénticos en esta VM; firma JAR v1 de laboratorio
comprobada. Inventario: un DEX, 17 referencias de tipo externas y sin JNI.
Ver su README y reports/a0-fixture/. La siguiente puerta es ejecutar ese DEX
y resolver sus APIs fuera de Android, antes de afirmar compatibilidad de interfaz.

## Primer motor probado

ART host de las pruebas oficiales de R8 ejecuta nuestro DEX semántico en Linux,
sin arrancar Android. Al cargar la APK original, el enlazador encuentra
MainActivity y falla explícitamente al resolver android.app.Activity. Es evidencia
del motor y de la siguiente dependencia, no de ejecución funcional de la APK.
Ver ESTUDIO-ART-HOST.md y reports/a1-art-host/. Ese primer ensayo no cerró A1/A2;
el ensayo posterior con el subconjunto de API se describe a continuación.

## DEX de la APK ejecutado con API mínima

runtime/apk añade el subconjunto necesario sin recompilar la aplicación. La APK
original ejecuta su creación y listener en ART: 0→1→2, cierre, nuevo proceso 2→3.
Los textos se leen del recurso binario; una variante sin firma con DEX idéntico
cambia el texto observado. Se comprueban bloqueo de datos, permisos, recursos
truncados y preferencias corruptas. Ver reports/a1-counter-headless/ y
CONTRATO-APK.md. Esta prueba cierra A0/A1 para la fixture medida; A2, el resto de
aplicaciones, estabilidad, seguridad y distribución siguen pendientes.

## Ventana y entrada verificadas; dirección del port

archtv-apk-host representa el árbol real en Wayland. La prueba de
reports/a2-wayland/ verifica entrada uinput, persistencia entre sesiones, cierre
y coincidencia exacta del frame del cliente con el buffer DRM capturado.
Ver APK-WAYLAND.md. La implementación android.* sigue siendo un subconjunto
propio: el usuario pide ahora priorizar el port selectivo del framework original
de AOSP a Linux. Esta prueba se mantiene como regresión, sin confundirla con un
port ya realizado ni introducir el arranque de Android como requisito.

PORT-FRAMEWORK-AOSP.md define la secuencia del port original: cierre de compilación
de Looper/Handler/Message/MessageQueue, JNI Linux, recursos originales y después
vistas/ventanas/ciclo de vida. Hay 17 fuentes fijadas con hashes e inventario
reproducible; el primer resultado de compilación se detalla a continuación. Las puertas
A0–A2 verificadas describen el prototipo propio, no este trabajo nuevo pendiente.

El primer conjunto original (Looper/Handler/Message/MessageQueue) ya compila sin
modificar fuentes y llega en ART hasta MessageQueue.nativeInit, aún sin enlace
JNI. La cola no es funcional todavía. Ver runtime/aosp/README.md y
reports/aosp-queue-compile/. El contador sigue usando el prototipo previo.

El JNI Linux Rust de MessageQueue ya está probado en ART, incluyendo despertar
entre hilos y listener FD público con SparseArray/utilidades originales. El
despacho Handler/Looper.loop falla todavía por Parcelable ausente. AOSP-JNI-LINUX.md
y reports/aosp-queue-jni/ registran esta frontera; no se da por completado el port.

Handler.post y Looper.loop originales ya despachan mensajes en modo Linux local.
Pasan FIFO, diferidos, cancelación, idle, WorkSource, hilos cruzados, barreras,
quit y quitSafely, con diez procesos nuevos. Ver AOSP-HANDLER-LINUX.md y
reports/aosp-handler-foundations/. Falta integrar este bucle en la APK y portar
Activity/View/recursos y servicios restantes. El primer timeout del comprobador
se conserva sin causa atribuida; H7 sigue abierto.

## La APK ya usa el principal original

El runtime combinado usa prepareMainLooper y Handler originales para creación,
activaciones y cierre. Pasan ráfaga de 64 comandos con 16 pendientes, EOF, error
y recuperación, además de DRM/Pixman y entrada uinput con persistencia 2→3.
Ver APK-LOOPER-AOSP.md, reports/aosp-ui-headless/ y reports/aosp-main-ui-wayland/.
La biblioteca nativa se exige explícitamente. Activity/View/Bundle/recursos y
preferencias siguen propios; el framework completo y las puertas finales siguen abiertos.

## Recursos originales: JNI aislado

AssetManager.getResourceText, ApkAssets y StringBlock originales ya resuelven
los textos del contador en ART mediante libandroidfw original. Pasan la variante
con el mismo DEX y los rechazos de tablas truncadas/rutas ausentes; la regresión
de relojes/Handler/colas pasa con el conjunto ampliado (10 procesos de semántica).
Ver AOSP-RECURSOS-LINUX.md y reports/aosp-resources-jni/. Sigue pendiente conectar
el proveedor usado por la APK, inicializar los recursos de sistema y portar
Resources/Activity/View. Este hito no cierra A3–A5 ni las puertas generales.

La integración del proveedor de recursos en el contador ya sustituye el parser
propio. Pasan la regresión headless y dos sesiones nativas DRM/Pixman con entrada
y coincidencia exacta de capturas: reports/aosp-resources-headless/ y
reports/aosp-resources-wayland/. Persisten los pendientes de recursos de sistema,
Resources y Activity/View originales, servicios, estabilidad y distribución.

Resources público ya construye su implementación original y ejecuta getString,
configuración/densidad y RTL sobre Linux. Ver AOSP-RESOURCES-PUBLICO.md y
reports/aosp-public-resources/. Falta integrarlo en el contador, inicializar
recursos de sistema y reconstruir los cuatro bindings sysprop precompilados
registrados; el resto del port y las puertas generales siguen abiertos.

El contador ya integra Resources público y el perfil inmutable x86_64/API 33.
Pasan regresión headless, conflicto de propiedades externas y dos sesiones
DRM/Pixman con entrada/persistencia y capturas idénticas. Ver
reports/aosp-public-resources-headless/ y reports/aosp-public-resources-wayland/.
La inicialización de sistema, métricas dinámicas, reconstrucción de bindings y
port de Activity/View/servicios siguen pendientes, junto con las puertas generales.

Métricas iniciales de Resources verificadas con configure Wayland real a 720p y
1080p, entrada/persistencia y capturas exactas. Los cambios de tamaño del runtime
pasan en headless. El resize en vivo después del primer frame también pasa en Wayland anidado;
continúan pendientes HiDPI/hotplug y cambio físico de modo DRM; ver AOSP-METRICAS-WAYLAND.md y reports/aosp-display-*.

Context/ContextWrapper/Application originales integrados: 54 fuentes originales,
seis hooks Linux funcionales y 126 abstractos rechazados explícitamente. Se retiró
el Context propio; pasan contador, wrapper/callbacks, DRM y resize anidado. Ver
CONTEXTO-AOSP-LINUX.md y reports/aosp-context-*. No cierra ContextImpl, servicios,
Activity/View originales ni las puertas generales de estabilidad/distribución.

## Segunda APK: contexto y configuración observados por la aplicación

La APK independiente fixtures/apk/context-metrics usa sólo el SDK público y
verifica Resources/Application originales desde su Activity. Pasan configuración
horizontal/vertical en ART y resize Wayland real con texto y callbacks actualizados
por la aplicación. Fuentes, APK, toolchain y evidencias están fijados en
reports/aosp-context-metrics/ y su README. Amplía la cobertura del port; no cierra
A3/A4 ni el port pendiente de Activity/View originales.

El port de vistas dispone ya de un modo de compilación de View/ViewGroup y
ContextThemeWrapper originales. El diagnóstico ART deja explícito que sólo se
carga ContextThemeWrapper: las otras dos clases y su integración siguen
pendientes. Ver AOSP-VISTAS-LINUX.md; no cambia las puertas A2/A3 del port.


El diagnóstico posterior ya inicializa View/ViewGroup/ContextThemeWrapper
originales, con pruebas de StateSet y helpers de tamaño sobre ART. Se genera el
binding de estados desde XML AOSP original, sin añadir bytecode de la referencia.
Ver reports/aosp-views-initialization/. La construcción y dibujo de View original
y la sustitución de la jerarquía propia siguen abiertos.


El ensayo del constructor real de View con contexto Linux y recursos originales
del APK está documentado en AOSP-CONSTRUCTOR-VIEW.md. Las dependencias originales
amplían el conjunto a 73 fuentes y permiten avanzar hasta el JNI ausente de
Log.isLoggable. La View todavía no se construye; la regresión estática sigue
pasando. Ver reports/aosp-view-constructor/.


Log original ya enlaza sus tres métodos JNI con stderr Linux y filtrado de
prioridad probado en ART; ver AOSP-LOG-LINUX.md y reports/aosp-linux-log/. Pasa la
regresión headless del contador. El constructor View con el conjunto de 74 fuentes
avanza hasta config_scrollbarSize del sistema, todavía ausente. Cargar recursos
de sistema y completar construcción/dibujo siguen pendientes.


El perfil de 18 recursos de sistema AOSP ya carga junto con el APK, preservando
IDs y valores originales. Pasan lectura de los 18 valores a 160/320 dpi, cookies
de sistema/aplicación y regresiones de contador/métricas. El constructor View
avanza hasta WindowManagerGlobal, aún ausente. AOSP-RECURSOS-SISTEMA.md y
reports/aosp-system-resources/ registran el alcance parcial y la frontera de
servicio de ventanas; no se acredita construcción ni dibujo de View original.


El conjunto de 82 fuentes originales ya ejecuta la caché de ServiceManager con un
endpoint local de lifecycle real. Se genera IWindowManager íntegro desde 67
contratos AIDL originales: coinciden 133 firmas e IDs de transacción y cargan sus
cuatro clases en ART. AOSP-SERVICIOS-LOCALES.md y reports/aosp-service-bootstrap/
registran esas pruebas. El constructor View llega al contexto global Binder aún
sin enlazar; faltan el servicio de ventanas conectado a Rust/Wayland y la
construcción/dibujo de View. No se acredita IPC Binder ni interfaz APK original.


Siete consultas IWindowManager ya leen el estado real publicado por el anfitrión
Rust tras configures Wayland. Pasan 960×540→800×450, tamaño inicial, densidad y
políticas, junto con el cierre del proveedor. El contrato conserva 126 métodos
explícitamente pendientes. El constructor View con ese servicio supera la
resolución de window y llega a ValueAnimator, aún ausente. Ver
AOSP-VENTANAS-WAYLAND.md y reports/aosp-window-wayland/. El servicio se prueba en
un proceso ART separado; el bootstrap en Main y dibujo original siguen pendientes.


El conjunto de 97 fuentes originales ya aplica la política de animación del host
a ValueAnimator original y verifica sus callbacks e interpoladores Java. El
contexto visual se asocia explícitamente al display virtual validado. View supera
esas rutas y llega al JNI RenderNode.nCreate, aún sin portar; no se crea una View
funcional. AOSP-ANIMACION-CONTEXTO.md y reports/aosp-animation-context/ conservan
las pruebas Wayland, el rechazo de display en modo headless y las regresiones.
El reloj de animación, gráficos nativos, integración APK y distribución siguen
pendientes.

El primer paso nativo HWUI compila 14 unidades originales, incluido RenderNode
y su JNI, usando fuentes Skia y dependencias host fijadas por archivo. Ver
AOSP-RENDERNODE-NATIVO.md y reports/aosp-hwui-host-objects/. Faltan el enlace de
las bibliotecas, resolver la ABI CriticalNative en ART, ejecutar y presentar
gráficos originales; A3 no se considera terminado por esta compilación.

Las once factorías nativas originales de interpolación ya se ejecutan en ART
con 222 objetos creados/evaluados/liberados y 3102 muestras, incluyendo paridad
Java/C++ de dos curvas. AOSP-INTERPOLADORES-NATIVOS.md y su informe registran
esta prueba separada. El bootstrap del runtime APK, CriticalNative de RenderNode,
el reloj de frames y dibujo siguen pendientes. La construcción Skia continúa;
no se acredita A3 completo ni estabilidad general con estos ciclos de prueba.

Skia host CPU original ya completa su construcción y ejecuta Canvas nativo con
3072 píxeles comprobados mediante dos lecturas y salida PPM. El informe
aosp-skia-raster conserva archivos, hashes y verificación posterior de fuentes.
Esta prueba C++ no carga Canvas Java/RenderNode en ART ni presenta una ventana;
continúan pendientes el enlace HWUI, integración APK, GPU y las puertas A3–A5.

El enlace HWUI/Minikin y el perfil RenderNode de 16 JNI ya pasan en ART con 64
objetos originales y propiedades independientes. AOSP-RENDERNODE-ART.md y el
informe aosp-rendernode-native conservan los resultados. Pasan también resize
Wayland y cierre del proveedor; View avanza hasta getApplicationInfo ausente.
Todavía no se construye una View funcional ni se dibuja el APK con esas clases.
Quedan metadata APK, las otras entradas, callbacks, lifecycle y dibujo/GPU; este
avance no cierra A3 ni los requisitos de estabilidad/distribución.

ApplicationInfo original ya obtiene paquete, SDK y metadata de la APK mediante
androidfw/ZIP originales, con UID y rutas Linux. Pasan dos APK target 27/28,
rechazos de XML inválido/SDK superior/expansión y regresiones. El perfil añade
el foco original (19 recursos); View avanza hasta GradientDrawable ausente.
AOSP-METADATOS-APK.md e informes aosp-application-info registran el alcance;
no se acredita todavía View funcional ni dibujo original del APK.

El constructor de View original ya termina en ART tras incorporar GradientDrawable,
PorterDuff, BlendMode y Xfermode sin modificar. AOSP-DRAWABLE-BOOTSTRAP.md y
reports/aosp-drawable-bootstrap registran el estado inicial y la regresión de
Wayland. No hay todavía dibujo de la View original ni sustitución de las vistas
propias del contador; measure/layout, widgets y presentación siguen pendientes.

View.measure original pasa cinco casos de restricciones y mínimos tras incorporar
LongSparseLongArray original. El layout avanza a AccessibilityManager ausente;
AOSP-VIEW-MEDIDA.md describe contratos, permisos e identidad pendientes antes de
su adaptación. El resize Wayland sigue pasando; no se acredita layout completo,
accesibilidad, dibujo original ni cierre de A3.

AccessibilityManager y UserHandle originales compilan; sus dos contratos AIDL
completos coinciden con la referencia fijada. Pasan consultas de permisos sin
concesiones y regresiones de medida/Wayland; layout avanza a la asignación nativa
de Binder original, aún ausente. AOSP-ACCESIBILIDAD-CLIENTE.md registra la política,
la colisión UID Linux/Android y el ciclo de vida nativo pendiente. No se acredita
accesibilidad, aislamiento ni layout completo.

El holder Binder original ya compila/enlaza en Linux y permite 32 Binder originales
en ART con interfaces locales. Pasan 12.800 asignaciones/liberaciones nativas
mediante el finalizador AOSP, sin fugas detectadas por LSan en esa prueba. El
layout supera el cliente AIDL y se detiene en LineBreakBufferedWriter al registrar
el fallback de foco. AOSP-BINDER-HOLDER.md distingue las pruebas nativas del GC
ART y mantiene pendientes transporte, layout completo y dibujo original.

Log original ya formatea excepciones mediante LineBreakBufferedWriter original;
pasan cuatro regresiones de filtros y el caso adicional de causas, Unicode,
supresión de red, DeadSystemException y línea ASCII de 12.000 caracteres. El
layout supera el registro del fallback de foco y se detiene ahora en la búsqueda
de servicios: BinderInternal.getContextObject ausente. AOSP-LOG-EXCEPCIONES.md
registra el alcance y mantiene layout/dibujo original y A3 pendientes.

### Bootstrap original aislado · 2026-10-30

A3 sigue abierto. El [ensayo](../reports/aosp-isolated-bootstrap/result.json)
con Markor intacta alcanza ActivityThread, pero falla en ContextImpl antes de
ejecutar la aplicación: faltan módulos originales del framework. Siguiente
puerta: classpath modular coherente con implementaciones originales, después
Application.attach/onCreate originales y recorrido de nota completo. No usar
stubs del SDK como runtime. Namespace UID 10000 y comprobaciones parciales
pasan; aislamiento completo, presupuestos y todas las etapas reales siguen
pendientes. A4/A5 no se cierran.

### Framework modular original · 2026-10-30

A3: el [nuevo ensayo](../reports/aosp-platform-bootstrap/result.json) utiliza
24 jars no básicos originales de una única imagen, con core/JNI host separado.
ContextImpl se inicializa; PackageParser falla por nativeOpenXml sin enlazar.
Prioridad: reutilizar JNI original de recursos/XML y continuar Application
original y recorrido completo de Markor. El límite anterior de TetheringManager
queda superado en este perfil, no mediante stubs. A4/A5 y H7–H9 siguen abiertos.


<!-- Fin del registro histórico conservado. -->

## R1/R2 · progreso del recolector, no aceptación de servicios

[Hito y límites](../reports/android16-child-reaper/findings.json): el coordinador
Bionic registra Service::GetSigchldFd antes de StartPropertyService y reutiliza
ReapAnyOutstandingChildren. Una instancia por proceso y Epoll; cierre elimina el
handler, cierra FD y restaura máscara después de unir workers. libprocinfo completo
original enlazado, sin sustituir su consulta procfs. REA observa hijos getprop0 y
false1 recogidos (ECHILD), FD4→4; supervisor Rust conserva su protocolo diagnóstico.
Pendientes: hijos registrados ServiceList/Service::Reap, colas ctl autorizadas,
clases, cgroups, mapeo UID, critical/onrestart/reinicio y gestión de descendientes.
No ejecutar cohortes originales como aceptadas hasta resolver R1-MAC; Start o
SIGCHLD funcional no prueban readiness. Matriz APK y R6 ARM sin cambios.

## R1/R2 · fallo original de Start antes de fork

[Contraste nativo](../reports/android16-service-start-gate/findings.json): el perfil
servicemanager original llega a Service::Start y falla por getcon antes de fork;
PID0/no running/ECHILD, FD4→4. No omitir MAC ni suplir etiquetas. Linux necesita
política explícita de fallos: Start resetea flags antes de validar y su scopeguard
puede ejecutar reboot_on_failure en otros perfiles. Un error no es rollback
transaccional y un Start correcto tampoco prueba exec/Binder/readiness.
Pendientes originales: identidades/cgroups/contextos, hijo registrado y Reap,
restart/critical/onrestart y cohortes autorizadas; recorrido completo Markor abierto.

## R1/R2 · política de cohorte basada en declaraciones originales

[Auditoría](../reports/android16-service-effect-audit/findings.json): observador
SectionParser delega ServiceParser/ActionParser originales y conserva tokens, origen
y orden sin invocar handlers; imports originales observados y override histórico
separado de campos públicos finales. No parche adicional ni gramática RC propia.
No es admisión ni política efectiva: admission_status=not_evaluated. Errores de
parseo suprimen todo manifiesto aunque AOSP retenga ServiceList parcial.
Puertas pendientes: fijar/hashar clausura de imports antes de admisión; establecer
alcance de class_restart y fallos críticos/reboot_on_failure bajo Linux; preservar
onrestart/setprop y perfiles/FD/capabilities. Referencias apexd, audioserver,
gatekeeperd y surfaceflinger ausentes de esta cohorte no deben borrarse ni darse
por satisfechas. Evaluar grupos completos originales con MAC/identidades/cgroups
y readiness real; no arrancar init Android general. Pruebas de auditoría propias
no cierran etapas APK ni sustituyen el recorrido Markor.

## R1/R2 · fallo original con receptor Linux

[Integración y límites](../reports/android16-linux-failure-sink/findings.json):
Linux instala trigger_shutdown antes de operaciones de servicios; retiene primer
fallo y entrega datos hex acotados al canal Rust, nunca ejecuta el texto. Petición
mayor de24 bytes tiene error explícito. Rust no permite que un ACK posterior
convierta el fallo en arranque; wait_failed recoge salida no cero con pidfd/wait.
MCP verifica scopeguard original de Start por getcon y salida69; worker diagnóstico
conserva cierre0. Receptor sólo serializado; envío/protocolo no constituye monitor
asíncrono ni política de recuperación. LOG(FATAL) crítico no recorre este callback
y sigue pendiente. No quitar critical/onrestart ni aceptar cohortes antes de
resolver identidades/cgroups/MAC y dependencias originales. Fixtures de fallo no
acreditan servicios/APK completos; Markor y matriz real siguen abiertos.

## R1-MAC · estado posterior al arranque SELinux autorizado

[Verificación actual](../reports/android16-selinux-permissive-boot/findings.json):
LTS6.18.59 con SELinux LSM activo, permisivo, policyload0, formato soportado35 y
contexto inicial kernel. Host sin selinuxfs; montajes privados de lectura permiten
observar página virtual y repetir sonda Binder idéntica. MCP control/SID0 ahora
recibe BR_TRANSACTION_SEC_CTX y respuesta con PID/UID correctos; no inspecciona
el texto SID. El fallo-95 previo con LSM inactivo queda como evidencia histórica.
No hay política/etiquetas/transiciones/enforcement ni gestor/APK aceptado.
Revalidar cada arranque: selección puntual no equivale a despliegue persistente.
Política Linux compatible y rollback requieren validación antes de cualquier
carga; no se carga política ni se inventan contextos en esta verificación.

## R1-MAC · entrada Linux→coordinador original no resuelta

[Evaluación original offline](../reports/android16-policy-launch-transitions/findings.json):
la política candidata conserva tres cálculos Android originales seleccionados,
pero no selecciona transición desde Linux init_t/kernel_t hacia init_exec o
servicemanager_exec Android. Contexto calculado igual al emisor no es denegación;
Service::ComputeContextFromExecutable original lo rechazaría antes de fork.
El init Android además tiene denegados compute_create/compute_av y accesos al
security_t Linux. Transición y entrypoint Android init→servicemanager sí permitidos
en las consultas; el acceso desde Linux y la interfaz real siguen ausentes.
Puerta siguiente: definir sujeto Linux real y entrada explícita al coordinador
Android (usuario/rol/tipo/MLS, etiqueta ejecutable, FD/capacidades/namespaces),
mediación libselinux completa y denegaciones, conservando aserciones. No otorgar
dyntransition global ni convertir dominios en permisivos para pasar pruebas.
Validar también despliegue/recuperación antes de carga. Doce cálculos y doce
consultas no prueban exec/enforcement/servicios/APK ni equivalencia general.

## Evolución previa de la priorización (histórico)

La [revisión de zygote original](../reports/android16-zygote-security-contract/findings.json)
obliga a evaluar NNP y capacidades como contrato de cohorte: seccomp se instala
antes de perder privilegios; la fuente advierte de transiciones SELinux al usar
NNP como alternativa. Las ramas permisivas examinadas omiten filtros. No basta
un arranque permisivo exitoso ni añadir process2 a cada fallo. Mantener controles
actuales hasta justificar/probar una alternativa completa, sin cambiar seguridad
del anfitrión. Próximo inventario: seapp/seccomp, RC/capabilities de gestores,
stdio/dispositivos, FD y cgroups; luego S0–S2 y pruebas autorizadas.

R1/R2: [framing del supervisor corregido](../reports/android16-supervisor-framing/findings.json),
19 regresiones Linux pasan; mensajes parciales y fallo terminal preservados.
Pendiente monitor de fallos posteriores al arranque/salida con pidfd y canal,
incluso si un descendiente conserva FD. No acredita servicio o APK. Exigir
contexto seapp real y filtros efectivos: retorno0 en permisivo no es aislamiento.

### Preparación de seguridad anterior (histórico; no estado vigente)

Seguir el [plan canónico de seguridad y recuperación](ARQUITECTURA.md#plan-de-seguridad-y-recuperación-del-anfitrión):
S0 recuperación → S1 contrato completo offline → S2 preflight anfitrión → S3 carga
permisiva sólo con autorización explícita → S4 enforcing sólo tras pruebas y nueva
autorización → S5 gestores y recorrido Markor. En aquella revisión S0–S2 aún abiertos; no había solicitud
de carga/enforcing preparada. El arranque anterior no los autoriza.
El [prototipo de entrada S1](../reports/android16-policy-launcher-entry/findings.json)
compila offline con aserciones activas: rol exclusivo y contexto exec Android
conservan transiciones de gestores y denegaciones seleccionadas; la variante
automática conserva identidad Linux y no valida el contexto del servicio siguiente.
No hay carga/exec real ni bootstrap de host, ni sustitución del perfil base.

La [auditoría del actor](../reports/android16-launcher-permission-audit/findings.json)
distingue54 potenciales reglas de salida/633 de entrada de27 decisiones concretas.
S1 sigue abierto. El [bootstrap offline](../reports/android16-launcher-bootstrap/findings.json)
modela productor init_t, entrada tipada/rol y supervisor Rust padre: 51 consultas,
cuatro compilaciones con aserciones. No hay productor real probado. Seis permisos
NNP/nosuid hacia gestores siguen denegados. Revisar el contrato completo
init/servicios/zygote y la colocación de credenciales/NNP; no desactivarlo ni
sumar excepciones aisladas. Procedencia/instalación del ejecutable, FD/stdio/pidfd,
etiquetas/dispositivos/cgroups y recuperación siguen pendientes de S0–S2.

La [inspección nativa actual](../reports/android16-postboot-mac-readiness/findings.json)
confirma getcon kernel, getfilecon ENODATA sin demostrar etiqueta efectiva y lectura status real sólo
tras configurar montaje RO explícito. Systemd -SELINUX exige integración de host.
Mantener controles originales/RC/cohortes; avance independiente de lectura/offline
permitido. Las nueve etapas Markor y todas las aplicaciones reales siguen abiertas.
