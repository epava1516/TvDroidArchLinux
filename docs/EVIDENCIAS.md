# Índice de evidencias

- [R1: clausura estática del servicio de propiedades](../reports/android16-property-service-closure/findings.json): raíz StartPropertyService enlaza; delta268 símbolos, SecondStageMain ausente, ninguna ejecución nueva. Fuentes originales contrastadas, fronteras supervisor/MAC/persistencia y riesgo ACK/durabilidad identificados. Mapa histórico regenerado tras redirección accidental, ejecutable original idéntico; hash histórico del mapa desconocido. [Checkpoint actual](../reports/android16-property-service-closure/checkpoint.json).

- [R1-MAC: hwservicemanager original ejecutado](../reports/android16-hwmanager-start/findings.json): identidad/grupos RC, binario GSI y cuatro fuentes/config contrastados; captura REA MCP salida127 por contexto SELinux propio ausente, tras leer contextos hwservice. VINTF vendor incompleto y advertencia libvintf diferenciados del fatal. Sin registro/readiness/IPC/APK aceptados. [Checkpoint del hito](../reports/android16-hwmanager-start/checkpoint.json).

- [R3: Composer original enlazado y espera de gestor](../reports/android16-composer-link/findings.json): tres unidades/tres enlaces estrictos; REA MCP observa espera real hwservicemanager.ready hasta límite/señal9, no disponibilidad. Binder privado separado y logs observados, sin HAL/registro/buffers/frames/APK. Preflight host aún falla. [Checkpoint del hito](../reports/android16-composer-link/checkpoint.json).

- [R3: enlace libui y ejecución nativa](../reports/android16-libui-link/findings.json):23 unidades recompiladas con -fno-rtti original y dos dependencias estáticas; enlace estricto con30 proveedores originales GSI. REA MCP observa salida0 y libui fuente mapeada, regiones/transformación/sentinel NO_FENCE. No buffers, fence real, servicio, frames ni APK. [Checkpoint del hito](../reports/android16-libui-link/checkpoint.json).

- [R3: implementación original libui](../reports/android16-libui-implementation/findings.json):23 unidades fuente intactas compilan; siete familias HIDL allocator/mapper, diez hashes congelados y allocator AIDL V2. No enlace, equivalencia Soong, buffers, servicio ni APK probados. [Checkpoint del hito](../reports/android16-libui-implementation/checkpoint.json).

- [R3: entradas libui y codecs originales](../reports/android16-libui-source-closure/validation.json): herramienta fuente AIDL SDK36;31 IDL/124 archivos,32 objetos nativos incluido ComposerResources, dos bibliotecas enlazadas estrictamente y regresión AParcel local con FD/metadata ejecutada0 mediante REA MCP. Sin transferencia Binder, libui completo, HAL, frames ni APK. [Checkpoint del hito](../reports/android16-libui-source-closure/checkpoint.json).

- [R3: bindings y servicio fuente](../reports/android16-hidl-native-bindings/validation.json):14 unidades de transporte Bionic y servicio/HwcLoader/framebuffer compilan; recursos falla por libui no suministrada. Fuente Git recuperada y agrupación original libhidlbase identificada, ELF estático por REA MCP. Sin link/servicio/dispositivo/frames/APK. [Checkpoint del hito](../reports/android16-hidl-native-bindings/checkpoint.json).
- [R3: HIDL host y generación](../reports/android16-hidl-generator/validation.json):66 unidades, nueve hashes de archivos .hal comparados con current.txt/Python,39 fuentes/cabeceras generadas y cuatro hashes Composer observados por REA MCP. No certifica parser/ABI, bindings nativos, HAL, frames ni APK. Descarga loader parcial HTTP429 documentada. [Checkpoint del hito](../reports/android16-hidl-generator/checkpoint.json).
- [R3: módulos vendor originales y sphal](../reports/android16-vendor-libutils/validation.json):69 fuentes originales intactas, cinco bibliotecas enlazadas estrictamente y libc++ prebuilt seleccionado por fuente; carga/descarga originales0 y seis paths vendor mapeados en ejecución REA MCP. Sin equivalencia Soong completa, HIDL/dispositivo/frames/APK. [Checkpoint del hito](../reports/android16-vendor-libutils/checkpoint.json).
- [R3: carga vendor sphal](../reports/android16-hwc-vendor-load/validation.json): ejecución MCP Bionic real; namespace visible pero android_load_sphal_library falla por libutils.so, mismo adaptador del control plataforma. Namespace intacto; errores del arnés separados. Sin HAL/frames/APK aceptados. [Checkpoint del hito](../reports/android16-hwc-vendor-load/checkpoint.json).
- [R3: HWC2On1 original build/load](../reports/android16-hwc2on1-build/validation.json): dos fuentes completas intactas, enlace compartido estricto y dlopen NOW/dlclose0 nativos observados por REA MCP, UID10000/caps0. No vendor/Soong equivalente, dispositivo HAL, sync, frames ni APK aceptados. [Checkpoint del hito](../reports/android16-hwc2on1-build/checkpoint.json).
- [R3: reutilización Composer](../reports/android16-composer-reuse/validation.json): commits/blobs comprobados; adaptador HWC2On1 original retenido en A16, HAL Wayland acoplado a interfaces propias, Composer DRM requiere KMS master. Licencias parciales y siguiente comparación de adaptación explícitas; ninguno construido/ejecutado. [Checkpoint del hito](../reports/android16-composer-reuse/checkpoint.json).
- [R3: contrato SF/Composer](../reports/android16-surfaceflinger-contract/validation.json): siete fuentes originales verificadas, ELF original mediante REA MCP y48 dependencias directas con candidatos. Composer real/hotplug inicial necesarios; sin ejecución gráfica, HAL ni APK aceptados. [Checkpoint del hito](../reports/android16-surfaceflinger-contract/checkpoint.json).
- [Contraste SID nativo](../reports/android16-binder-secctx-probe/validation.json): sonda propia, transacción sin SID con PID/UID correctos; con SID BR_FAILED_REPLY y error extendido -95. Misma imagen Bionic, capturas MCP, primer fallo del arnés conservado; sin aceptación MAC/gestor/APK. [Checkpoint del hito](../reports/android16-binder-secctx-probe/checkpoint.json).
- [Binder Rust y 13 pruebas originales](../reports/android16-binder-kernel-contract/validation.json): ejecución nativa Bionic observada por REA MCP; cinco casos de gestor excluidos. SID de transacciones obligatorio por fuente. Sin aceptación de IPC/MAC/APK; límites del oráculo y muestreo explícitos. [Checkpoint del hito](../reports/android16-binder-kernel-contract/checkpoint.json).
- [Contrato kernel upstream6.18.59](../reports/android16-kernel-policy-contract/validation.json): generador original;96 clases/1694 permisos cubiertos y11 SID numéricos coincidentes. Guarda del constructor, negativos AOSP/deriva y binario idéntico. Fuente/build/runtime del host diferenciados; no kernel/gestores/APK aceptados. [Checkpoint del hito](../reports/android16-kernel-policy-contract/checkpoint.json).

- [Constructor de política experimental](../reports/android16-policy-builder/validation.json): CIL/binario idénticos al candidato probado; tres rechazos CLI y timeout/limpieza de proceso verificados. Generación/compilación reproducible, sin instalación/carga/VM ni readiness de servicios/APK. [Checkpoint del hito](../reports/android16-policy-builder/checkpoint.json).

- [Consultas SELinux del gestor offline](../reports/android16-policy-manager-selinux/validation.json): tres reglas;28 casos especializados,17 previos y9 originales concuerdan;12 operaciones security restantes denegadas. Exportación completa añade sólo3 reglas, atributos iguales. Sin kernel/endpoints/servicio/APK aceptados. [Checkpoint del hito](../reports/android16-policy-manager-selinux/checkpoint.json).

- [Adaptador proc offline](../reports/android16-policy-proc-adapter/validation.json): ocho permisos recuperados, seis denegaciones conservadas, nueve decisiones originales iguales; atributos sin cambios y exportación con una regla añadida. Tres interfaces SELinux del gestor siguen denegadas; sin syscalls/servicios/APK aceptados. [Checkpoint del hito](../reports/android16-policy-proc-adapter/checkpoint.json).

- [Composición con universos explícitos](../reports/android16-policy-type-universe/validation.json): compilador0 con aserciones;439 atributos retenidos y nueve decisiones válidas coinciden con controles.100 atributos Linux ausentes ya en control aislado; búsqueda de proc Linux por app Android denegada. No política de despliegue ni APK. [Checkpoint del hito](../reports/android16-policy-type-universe/checkpoint.json).

- [Universos de tipos y aserciones](../reports/android16-policy-global-labels/validation.json): 47 sustituciones de etiquetas y27 SID declaradas; compilador emite14 marcadores neverallow antes del límite90s. Namespace insuficiente para not/all; sin política aceptada ni APK. [Checkpoint del hito](../reports/android16-policy-global-labels/checkpoint.json).

- [Hipótesis de SID y etiquetas globales](../reports/android16-policy-sid-ownership/validation.json): dos elecciones explícitas, ambas255 en genfscon;29 coincidencias literales de contexto. Reglas/aserciones conservadas, sin base seleccionada ni host/servicios/APK aceptados. [Checkpoint del hito](../reports/android16-policy-sid-ownership/checkpoint.json).

- [Namespace Linux y conflicto de SID](../reports/android16-linux-policy-namespace/validation.json): compilación0 y cinco consultas seleccionadas conservadas; composición con nombres Android originales rechazada por contextos SID múltiples (27 diferencias literales). Sin política elegida/cargada ni servicios/APK. [Checkpoint del hito](../reports/android16-linux-policy-namespace/checkpoint.json).

- [Control experimental de namespaces](../reports/android16-policy-namespace-controls/validation.json): AOSP con MLS global compila; nueve consultas renombradas coinciden, pero el nombre original service_manager falla. Sin política integrada ni aceptación de servicios/APK. [Checkpoint del hito](../reports/android16-policy-namespace-controls/checkpoint.json).

- [Decisiones offline con herramientas originales](../reports/android16-policy-semantic-baselines/validation.json): 10 inventarios y 14 accesos (6 permitidos, 3 denegados, 5 errores); límites de sepolicy-check/seamendc documentados. Sin enforcement ni APK. [Checkpoint del hito](../reports/android16-policy-semantic-baselines/checkpoint.json).

- [Investigación ARM/Native Bridge separada](../reports/arm-native-bridge-research/validation.json): contrato A16, ELF original mediante REA MCP y fuentes/metadatos de candidatos/licencias. Sin proveedor o ARM ejecutado, sin cambios x86_64 ni APK aprobada. [Detalle R6](TRADUCCION-ARM.md).

- [Comparación de política AOSP/Linux](../reports/android16-policy-base-comparison/validation.json): refpolicy fijada y compilada offline;136 clases contrastadas contra CIL. Composición global directa rechazada, sin descartar estrategias adaptadas. No política elegida/cargada ni APK. [Checkpoint del hito](../reports/android16-policy-base-comparison/checkpoint.json).

- [Requisitos Linux y política offline original](../reports/android16-host-security-preflight/validation.json): ocho regresiones del diagnóstico; VM no apta para gestores originales todavía. Herramientas SELinux host y CIL platform compilados, neverallow activo; sin carga/instalación/etiquetado ni APK. [Checkpoint del hito](../reports/android16-host-security-preflight/checkpoint.json).

- [Binder privado y puerta de política original](../reports/android16-binder-service-gate/validation.json): dispositivos distintos/protocolo8; ART llega a ActivityThread.main, sin Markor. Servicemanager original aborta por SELinux inactivo. No transacciones/servicios/política/APK aceptados. [Checkpoint del hito](../reports/android16-binder-service-gate/checkpoint.json).

- [Perfil original y creación VM fallida](../reports/android16-property-profile/validation.json): PropertyInit0, 170 valores iguales con lector UID10000/caps0; REA MCP/GDB prueba fallo de análisis de opciones dentro de JNI_CreateJavaVM, sin VM lista ni APK. [Checkpoint del hito](../reports/android16-property-profile/checkpoint.json).

- [PropertyInit original: enlace y fallo ejecutado](../reports/android16-propertyinit-entry/validation.json): 146 fuentes nativas protobuf/Abseil; enlace0, ejecución127 por entrada vendor de política ausente. No readiness, política o APK. [Checkpoint del hito](../reports/android16-propertyinit-entry/checkpoint.json).

- [Unidad libinit nativa y FFI Rust ejecutada](../reports/android16-libinit-native-unit/validation.json): 52 fuentes originales, archivo prototipo63 miembros; cuatro casos nativos Rust/Bionic ejecutados. No equivalencia Soong completa ni servicio/APK. [Checkpoint del hito](../reports/android16-libinit-native-unit/checkpoint.json).

- [Protoc original y esquemas init nativos](../reports/android16-original-protoc/validation.json):
  393 pasos del build anfitrión, salida0; protoc25.8 genera tres esquemas originales
  y descriptor, y sus fuentes C++ compilan para Bionic con clang21. Frontera por
  archivos, sin objetos glibc en target. El log completo conserva hash/ruta local.
  No enlazado de libinit ni IPC/persistencia/APK ejecutados. La sesión69923 terminó;
  [checkpoint actual](../reports/android16-original-protoc/checkpoint.json).

- [Generadores originales y contraste estático init](../reports/android16-original-generators/validation.json):
  adquisición de archivos con Git blob, errores/presupuesto/permisos probados;
  dos módulos ACONFIG generados con declaraciones/valores BP4A y compilados para
  Bionic. Paridad GSI desconocida. REA MCP/GDB observa región estática mediante
  minidebug, con avisos BFD conservados; sesión cerrada sin inferior. No ejecución
  de init/servicios/APK. [Checkpoint](../reports/android16-original-generators/checkpoint.json).

- [Bibliotecas originales de metadatos, ejecución Bionic](../reports/android16-native-property-libraries/validation.json):
  cinco fuentes de dos módulos, CRT y linker originales, wrapper existente
  ejecutado sin capacidades con UID10000 y namespaces originales. Generación
  repetida, rechazo de propietario y 4.145 lecturas cruzadas. Divergencia de 115
  bytes contrastada con [árbol completo](../reports/android16-native-property-libraries/layout-comparison.json);
  sólo cambia el orden de prefijos de igual longitud. No servicio/SELinux/APK.
  [Checkpoint](../reports/android16-native-property-libraries/checkpoint.json) conserva
  el build protobuf activo; evidencia REA estática separada de las ejecuciones.

- [Dependencias originales de libinit](../reports/android16-native-dependencies/validation.json):
  libcap nativo estático, sus seis fuentes y generadores originales; miembros
  ELF64 x86_64 verificados. Fuentes adicionales y fallo acotado de adquisición
  conservados. Sin ejecución libcap/libinit/servicio ni aceptación de permisos/APK;
  [checkpoint y build activo](../reports/android16-native-dependencies/checkpoint.json).

- [Construcción nativa libinit, parcial](../reports/android16-libinit-build/validation.json):
  adquisición desde lock, igualdad de 203 archivos init, compilador original21
  verificado por Git blob y objeto x86_64 con cabeceras Bionic/plataforma.
  Identidad libc++ mediante fuentes de selección, secciones y REA MCP; ELF
  completos distintos. Sondeo de las 52 unidades con hostclang23: 14 objetos,
  38 fallos; no aceptación del subsistema. Generador protobuf host en construcción,
  [handles y recuperación](../reports/android16-libinit-build/checkpoint.json).

- [Configuración boot original: inventario y decisión de unidad](../reports/android16-boot-profile/validation.json):
  tres prop files (101/21/58 declaraciones), tres contextos, dos raíces idénticas;
  metadatos originales idénticos al incluir todos los contextos presentes.
  [Decisión y cierre directo](../reports/android16-boot-profile/unit-decision.json),
  [fuentes fijadas](../reports/android16-boot-profile/sources.json) y
  [REA MCP exports de init](../reports/android16-boot-profile/rea-init-exports.json).
  Inventario/lectura estática y metadatos ejecutados, sin libinit/servicio/APK ejecutados.

## Entrada original de framework · fallo demostrado

[Validación](../reports/android16-framework-entry/validation.json),
[fuentes](../reports/android16-framework-entry/source-findings.json),
[baseline](../reports/android16-framework-entry/baseline/result.json),
[captura diagnóstica](../reports/android16-framework-entry/diagnostic-early-failure/entry.stderr),
[REA estático](../reports/android16-framework-entry/rea-startvm-disassembly.json) y
[checkpoint actual](../reports/android16-framework-entry/checkpoint.json).
Retorno0 original no acredita readiness: startVm falla antes de crear la VM por
ABI global ausente en el snapshot parcial. No JNI/framework ni APK aprobados.
La auditoría explica el requisito debug original sin declararlo satisfecho.
Markor sólo estuvo en classpath; la matriz mantiene las nueve etapas no probadas.

## Configuración nativa A16 · namespaces, classpaths y motor

[Validación](../reports/android16-linkerconfig/validation.json),
[procedencia de fábrica](../reports/android16-linkerconfig/factory-provenance.json),
[fuentes](../reports/android16-linkerconfig/source-findings.json),
[estricto global fallido](../reports/android16-linkerconfig/global-strict-failure/result.json),
[classpaths nativos](../reports/android16-linkerconfig/native-classpath/classpath),
[regresión DEX](../reports/android16-linkerconfig/semantic-regression/result.json) y
[checkpoint de namespaces](../reports/android16-linkerconfig/checkpoint.json).
36 módulos/4.395 archivos reproducidos; namespaces usados sin LD_LIBRARY_PATH ni
preload; 46 jars boot y 69 únicos de ejecución. ART estricto por APEX pasa, global
no: el modo normal ignora requisitos no resueltos. Fixture Java pasa, sin acreditar
ninguna etapa APK. REA identifica estáticamente los binarios, no observó su ejecución.
La extracción truncada por cuota se conserva con su causa y traslado verificado.

## Áreas de propiedades Bionic A16 · componentes ejecutados

[Validación](../reports/android16-property-area/validation.json),
[fuentes](../reports/android16-property-area/source-findings.json),
[escritor y errores](../reports/android16-property-area/areas-final/writer-privileged.json),
[getprop original](../reports/android16-property-area/clients-final/getprop.json),
[REA estático](../reports/android16-property-area/rea-property-set-disassembly.json) y
[checkpoint de áreas](../reports/android16-property-area/checkpoint.json).
101 valores exactos y tipos/contextos del snapshot oficial; UID10000 sin capacidades
antes de exec; 364 archivos repetidos. Se conservan fallos sin capacidades y de
namespace. Escritura por servicio falla por servidor ausente. No se acreditan
ART/DEX/APK ni enforcement SELinux.

## Configuración A16 · metadatos host y frontera de seguridad

[Validación](../reports/android16-configuration/validation.json),
[fuentes y dependencias](../reports/android16-configuration/source-findings.json),
[REA libc](../reports/android16-configuration/rea-libc-exports.json),
[kernel/identidades](../reports/android16-configuration/kernel-property-prerequisites.json) y
[checkpoint de metadatos](../reports/android16-configuration/checkpoint.json).
Siete tests originales pasan; 1.384 contextos generan bytes reproducibles y el
lector original aplica su control de propietario. REA acredita exports, no su
ejecución. Los ensayos host muestran etiquetado UID1000 denegado/UID0 permitido,
con SELinux inactivo: no se infiere enforcement. Servicio y áreas Bionic, generador
target, DEX, APK y aislamiento amplio siguen sin probar en este hito.

## Primeros componentes nativos A16 · ejecución parcial

[Procedencia GSI](../reports/android16-native-base/gsi-provenance.json),
[validación](../reports/android16-native-base/validation.json),
[fuentes contrastadas](../reports/android16-native-base/source-study.json),
[REA linker](../reports/android16-native-base/rea-linker-notes.json),
[REA ART](../reports/android16-native-base/rea-art-notes.json) y
[checkpoint de carga nativa](../reports/android16-native-base/checkpoint.json).
Archivo oficial/build/SDK36.1 y SHA coinciden. Linker help/list y ayuda ART pasan
tras añadir el APEX StatsD original entero; las primeras pruebas fallidas se
conservan. REA identifica ELF estáticamente; no observó ejecución. Los logs del
harness acreditan sólo esos comandos, con rutas aplanadas y configuración
original aún ausente. No hay DEX, APK completa, SF, CTS ni validación de seguridad.

## Fuente completa fijada · A16-QPR2-1

[Registro](../runtime/aosp/android16-qpr2/release.json),
[lock](../runtime/aosp/android16-qpr2/manifest.lock.xml),
[refs/procedencia](../runtime/aosp/android16-qpr2/manifest.lock.json),
[validación](../reports/android16-source-lock/validation.json) y
[checkpoint del hito de fuentes](../reports/android16-source-lock/checkpoint.json).
1.013 proyectos con commits exactos; XML repetido offline idéntico, input/caché
inválidos no aprueban lock. Diez objetos commit contrastados; build ID, main SF
y targets TV leídos a esas revisiones. No hay fuente completa sincronizada,
binarios ejecutados, prueba SF/Wayland ni nueva compatibilidad de APK.

## Entrada vigente · contrato Android16

[Checkpoint](../reports/android16-contract/checkpoint.json),
[verificación de versión](../reports/android16-contract/release-verification.json),
[REA MCP](../reports/android16-contract/rea-mcp-session.json) e
[índice de revisión](../reports/android16-contract/artifact-index.json).
Android16 QPR2/r4 está identificado; 1.013 refs ya fijadas en el hito de fuentes siguiente, todavía sin
aceptación de binarios/runtime A16. La revisión contractual se separa de código
pendiente. [Estudio API33 pausado](../reports/android16-contract/android13-study-summary.json):
su generador abortó por propiedades ausentes y el serializador host no enlazó;
no se presenta como snapshot de propiedades ejecutado ni como prueba A16.

El índice inferior conserva los alcances históricos y sus commits/hashes. Ninguna
fixture, clase, JNI o captura antigua acredita una APK completa sobre A16.

## Índices históricos y alcances originales


Este índice enlaza las afirmaciones del estado vigente; no duplica logs ni
convierte compilación/inspección en compatibilidad. Los hashes completos y commits
fuente están en [evidence-index.json](../reports/continuidad-20261030/evidence-index.json).
`git` es evidencia versionada; `local` sólo existe en esta máquina y requiere
verificación al retomar; `new` pertenece al desvío documental. El snapshot no es
un catálogo exhaustivo de todas las pruebas históricas del repositorio.

| Resultado | Evidencia | Alcance y limitación | Ubicación |
| --- | --- | --- | --- |
| fixture-wayland | [result.json](../reports/a2-wayland/result.json) | Fixture propia: ventana/entrada; no aplicación real general | git |
| metadatos | [result.json](../reports/aosp-application-info/metadata/result.json) | ApplicationInfo y cinco casos de metadatos; no PackageManager completo | git |
| rendernode | [result.json](../reports/aosp-rendernode-native/art/result.json) | Propiedades de RenderNode; no dibujo de APK original | git |
| binder-holder | [result.json](../reports/aosp-binder-holder/native-lifetime/result.json) | 12800 ciclos nativos; no GC ART ni IPC | git |
| log | [result.json](../reports/aosp-log-throwables/log/result.json) | Log: filtros y Throwable; no logd | git |
| registro-pendiente | [result.json](../dist/apk/local-registry-final-wayland-1/result.json) | Experimento versionado en b8ea156: registro local, layout/resize de View aislada; no dibujo de APK | local |
| binder-context-pendiente | [result.json](../dist/apk/binder-service-context-lifetime-1/result.json) | Experimento versionado en b8ea156: ciclo del holder extendido | local |
| rea-bundle | [rea-evidence.json.gz](../reports/continuidad-20261030/rea-evidence.json.gz) | MCP y análisis estático VLC/ELF; no ejecución ni compatibilidad | new |
| drm | [result.txt](../reports/h3/result.txt) | Histórico: DRM/entrada/VT en VM; no mando físico ni APK | git |
| sesion | [result.txt](../reports/h4/result.txt) | Histórico: foco y recuperación del shell; no compatibilidad APK | git |
| shell | [result.txt](../reports/h5-interactive/result.txt) | Histórico: recorrido shell/Foot/ajustes en VM; no runtime APK | git |
| paquetes | [runtime-root-verification.txt](../reports/h8-build/runtime-root-verification.txt) | Histórico: raíz de paquetes sin compiladores; no instalación del runtime APK actual | git |
| mcp | [rea-mcp-connection.json](../reports/continuidad-20261030/rea-mcp-connection.json) | Conexión MCP real e identidad observada; no compatibilidad de aplicaciones | new |

## REA MCP

El bundle comprimido contiene Evidence de esta sesión: inspección JADX de VLC
(`ev_746d40138a0f10e9c3202cd147e41d5efd4a7c58e81078c6109567a0bce77781`), inventario
APK (`ev_dcb26456aa926ea351cb253ef532b5433d5eeb9fe3da0a0aa58d86be7bef0f9c`) y notas
ELF del holder (`ev_cfbe375eab4797608dac9c739cf438cda9aec82776dde5d64e95f2eef5e25e06`).
MCP respondió como codex-mcp-client 0.165.0 / REA 6.8.0. VLC es org.videolan.vlc
3.7.1, minSDK 17, targetSDK 36, 15.261 clases y 2.618 recursos según el motor.
No se ejecutó la APK ni se verificó su firma en esa inspección. Las 30 declaraciones
de permisos no prueban concesiones ni uso efectivo; la estructura estática no
acredita comportamiento. La sesión de archivo se exportó y cerró.

## Historia y puertas abiertas

H0–H5: los informes originales se enlazan desde [ROADMAP.md](../ROADMAP.md) y sus
documentos de laboratorio. H6 Waydroid permanece histórico; no demuestra APK
sobre el runtime propio. H7 no está cerrado: faltan presupuestos completos,
soak y mandos físicos; el incidente de VM sigue documentado en
[INCIDENTE-VM-20261030.md](INCIDENTE-VM-20261030.md). H8/H9 conservan pruebas de
paquetes/ISO anteriores, no aceptación de instalación/actualización del runtime
APK actual. No hay resultado general de aislamiento ni compatibilidad amplia.

## Revisión de arquitectura y aplicaciones reales

El [índice de artefactos de la revisión](../reports/arquitectura-apk-20261030/artifact-index.json)
registra los hashes de resultados REA, dependencias ELF, matriz y ensayo de enlace
del framework. [La matriz](COMPATIBILIDAD-APK.md) fija Markor, Calculator y VLC;
las seis etapas funcionales siguen sin ejecutar. El ensayo
[framework-space](../reports/arquitectura-apk-20261030/framework-space/result.json)
sólo enlaza clases de dos APK sin inicializarlas, excluyendo android.* propios.
El [checkpoint de la revisión](../reports/arquitectura-apk-20261030/checkpoint.json)
conserva la revisión anterior; el snapshot de continuidad conserva
su propio alcance histórico. Ninguna de estas evidencias cierra compatibilidad.

## Bootstrap original aislado

[Resultado](../reports/aosp-isolated-bootstrap/result.json),
[hashes y procedencia](../reports/aosp-isolated-bootstrap/artifact-index.json) y
[checkpoint vigente](../reports/aosp-isolated-bootstrap/checkpoint.json). UID
10000 y preflight de namespace pasan; ActivityThread original se construye.
ContextImpl falla por TetheringManager ausente. Markor permanece sin ejecutar.
La fuente R8 exporta system/framework y APEX host; no acredita una plataforma
modular completa. El snapshot SDK de Connectivity lista stubs, no implementación
ejecutable. Ningún resultado cierra lanzamiento, UI, entrada, persistencia o
compatibilidad; los ensayos fallidos previos siguen en dist/apk local.

## Framework modular y parser original

[Resultado ART](../reports/aosp-platform-bootstrap/result.json),
[classpath original](../reports/aosp-platform-bootstrap/bootclasspath.json),
[validación](../reports/aosp-platform-bootstrap/validation.json) y
[checkpoint](../reports/aosp-platform-bootstrap/checkpoint.json). 31 jars con DEX,
orden y hashes reproducidos por dos extracciones del mismo archivo oficial.
ContextImpl pasa; PackageParser falla en nativeOpenXml. No se ejecutó código
de Markor. Se conservan logs pequeños y procedencia de imagen/módulos; el
[inventario de artefactos](../reports/aosp-platform-bootstrap/artifact-index.json)
registra hashes. REA MCP devuelve capability_unavailable para inspección Android
de JAR, documentado; no se atribuye esa inspección a MCP. Las APK reales analizadas
previamente conservan sus evidencias REA. La extracción no verifica firmas
AVB/APEX ni acredita distribución, compatibilidad nativa o seguridad.

## Revisión BASE-AOSP-1

[Checkpoint](../reports/base-aosp-x86_64-review/checkpoint.json),
[fuentes oficiales](../reports/base-aosp-x86_64-review/sources.json),
[índice y hashes](../reports/base-aosp-x86_64-review/artifact-index.json). El
ensayo JNI preservado sigue como código pendiente, separado de la revisión.
[Su error original](../reports/base-aosp-x86_64-review/pending-bootstrap.stderr)
demuestra ausencia de PermissionManager antes de ejecutar Markor. REA MCP verifica
una exportación JNI_OnLoad en ELF; [DocumentFile](../reports/base-aosp-x86_64-review/rea-markor-create-file.json)
y [VLC play](../reports/base-aosp-x86_64-review/rea-vlc-play.json) son contratos
estáticos. La traza externa MediaDrm no está disponible por clase SDK ausente
en APK y queda conservada, sin convertir el fallo de herramienta en compatibilidad.
Las búsquedas DEX sólo tienen su alcance declarado. Ningún flujo GMS/DRM ni
runtime target Bionic está probado por esta revisión.

## Primera prueba de componentes Bionic

[Checkpoint](../reports/bionic-component/checkpoint.json),
[resolución del launcher](../reports/bionic-component/linker-list-result.json),
[invocación ART target](../reports/bionic-component/art-core-result.json) y
[hashes](../reports/bionic-component/artifact-index.json). Linker original ejecuta
ayuda/listado con código 0; las 46 bibliotecas de la selección tienen cierre
estático. ART aborta 134 antes de la fixture por configuración pública ausente
en el harness, con namespaces generados todavía pendientes. No demuestra
compatibilidad de aplicaciones, servicios ni inviabilidad de Bionic. REA MCP
verifica notas/identidad ELF, no observa esa ejecución. No se arrancó Android.
