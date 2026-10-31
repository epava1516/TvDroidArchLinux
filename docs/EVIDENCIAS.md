# Índice de evidencias

## Primeros componentes nativos A16 · ejecución parcial

[Procedencia GSI](../reports/android16-native-base/gsi-provenance.json),
[validación](../reports/android16-native-base/validation.json),
[fuentes contrastadas](../reports/android16-native-base/source-study.json),
[REA linker](../reports/android16-native-base/rea-linker-notes.json),
[REA ART](../reports/android16-native-base/rea-art-notes.json) y
[checkpoint actual](../reports/android16-native-base/checkpoint.json).
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
