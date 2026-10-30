# Índice de evidencias

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
| registro-pendiente | [result.json](../dist/apk/local-registry-final-wayland-1/result.json) | Experimento sin commit: registro local, layout/resize de View aislada; no dibujo de APK | local |
| binder-context-pendiente | [result.json](../dist/apk/binder-service-context-lifetime-1/result.json) | Experimento sin commit: ciclo del holder extendido | local |
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
es el punto fechado más reciente; el snapshot de continuidad anterior conserva
su propio alcance histórico. Ninguna de estas evidencias cierra compatibilidad.
