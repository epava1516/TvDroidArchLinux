# Matriz de aplicaciones reales

La [integración actual de servicios originales](../reports/android16-selected-display/findings.json) falla aún en la ABI ashmem/memfd del kernel. No publica display ni modifica la aceptación de ninguna APK. ARM, servicios externos y DRM siguen siendo ejes separados.

## Evidencia de subsistemas · sin cambiar aceptación APK

[Recorrido nativo gráfico original probado](../reports/android16-software-renderer/sf-original-functional-findings.json): SurfaceFlinger y bootanimation originales dibujan mediante ANGLE/SwiftShader, allocator/mapper/HWC3, Wayland/Smithay y DRM, con consultas/identidades/cierre reales. Es dependencia previa; **no cambia ninguna de las nueve etapas de Markor u otra APK**, todas siguen no probadas. Permisivo no acredita aislamiento; Android completo no se arranca.

La prioridad actual es el [camino crítico Markor](ROADMAP-A.md#camino-crítico-vigente--markor-completo).
La integración negativa de propiedades/gestores no acepta ninguna de las nueve
etapas. ARM/GMS/DRM conservan sus ejes y requisitos; no bloquean este primer
recorrido salvo dependencia real demostrada de la versión/función seleccionada.

## Estado vigente A16-QPR2-1

La fuente canónica sigue siendo el JSON enlazado abajo, ahora schema 2. La base
es Android16 QPR2 nativa Bionic/AOSP, no el laboratorio Android13. Cada aplicación
registra nueve etapas: instalación, lanzamiento, interfaz, entrada, función
principal, persistencia, servicios, cierre y reapertura. Todas están **no probadas**
en A16; no se calcula porcentaje. Estados admitidos: aprobado, fallo demostrado,
bloqueo externo y no probado, siempre con base/versión/evidencia/alcance.

Markor, Calculator y VLC conservan versiones/hashes/procedencia y análisis estático.
Los bootstraps/fixtures/cierres nativos Android13 son historia, no resultados A16.
Se añaden como cobertura requerida Android TV/D-pad, aceleración/WebView/splits,
x86/ARM 32/64 y servicios OEM/privilegiados. Faltan artefactos y recorridos para
varios perfiles; no se inventan apps verificadas ni se limitan los casos a fáciles.

La misma base debe servir a categorías distintas sin reconstrucción por APK.
Registrar targetSdkVersion y uso de API posterior, firma/privilegios/OEM, tres
ejes API-servicios/ABI/ISA y requisitos remotos/hardware. No parchear APK para
eludir diferencias. La primera vertical es Markor, después R5/TV/multimedia;
el [contrato](CONTRATO-APK.md) y [roadmap](ROADMAP-A.md) definen la aceptación.

La [evaluación R6 de traductores](TRADUCCION-ARM.md) no modifica esta matriz.
Fijar variantes ARM originales del editor (sin repack ni fallback x86), motor y
guest bundle por separado antes de evaluar las mismas nueve etapas. Identificar
NativeBridgeItf o ejecutar una fixture no aprueba ninguna aplicación.

## Inventario de artefactos y evidencia previa


Fuente de los registros: [compatibility-matrix.json](../reports/arquitectura-apk-20261030/compatibility-matrix.json).
Contiene APK, versión/código, SHA-256, procedencia, SDK, bibliotecas nativas,
certificados declarados, Evidence IDs y resultados funcionales por app y base.
Las APK están intactas en caché local; no se recompilan ni se parchean.

| APK fijada | Perfil observado | Recorrido a verificar | Ejecución actual |
| --- | --- | --- | --- |
| Markor 2026.10.0, net.gsantner.markor | minSDK 21, target 35; no miembros lib/*.so en este APK | Crear/editar nota, entrada real, guardar, cerrar/reabrir | Nueve etapas sobre A16: no probadas |
| Calculator 1.4.0, org.fossify.math | minSDK 26, target 36; AndroidX Path para arm64/armv7/x86/x86_64 | Alias de lanzador, 2+3, historial/preferencias, cierre/reapertura | Nueve etapas sobre A16: no probadas |
| VLC 3.7.1, org.videolan.vlc | minSDK 17, target 36; VLC/medialibrary/C++ x86_64 | Fichero local, audio/vídeo, volver al shell, cierre | Nueve etapas sobre A16: no probadas en el runtime propio; Waydroid anterior no cuenta |

REA MCP/JADX observa respectivamente 4.985/5.023/15.261 clases; estos inventarios
no prueban cobertura dinámica. El ensayo del framework enlaza clases Activity de
Markor y Calculator sin inicializarlas: no aprueba etapas de la base vigente.
Un targetSDK superior a 33 tampoco demuestra incompatibilidad por sí solo; hay
que contrastar el uso efectivo/guardado de APIs con la versión del runtime.

Calculator y Markor se descargaron de releases oficiales y coinciden con el
SHA-256 publicado en sus assets. Para VLC se conserva la APK previa y su identidad;
no se volvió a validar su descarga original en esta auditoría.

REA inspecciona firmas declaradas y consistencia de digests, pero NO verifica
criptográficamente las firmas ni la autenticidad del firmante. Esos campos
permanecen explícitos como not_performed/unknown. Antes de una instalación de
producto se requiere verificación criptográfica y política de confianza.

No incluir .so en un APK no elimina JNI del framework, SQLite, renderizado o IME.
DT_NEEDED y notas ELF son evidencia estática, no carga ni reproducción funcional.
ARM-only, WebView, DRM comercial, Play Services, splits, hardware físico y estabilidad
prolongada siguen fuera de lo demostrado. Añadir versiones/ABI/casos a la matriz
sin convertir filas no probadas en compatibilidad ni usar fixtures como sustituto.

Las decisiones y la siguiente prueba están en [ARQUITECTURA.md](ARQUITECTURA.md);
el estado y roadmap conservan aislamiento, ligereza, instalación y actualización.

## Dependencias y selección de base BASE-AOSP-1

El JSON canónico incluye `dependency_catalog`, `dependency_profiles` por APK y
`required_coverage_cases`: registra contrato, código/bibliotecas candidatos,
adaptación, alternativas existentes, requisitos externos y resultados separados
de API/servicios, ABI Bionic/JNI e ISA. No duplica la aceptación en otro catálogo.

| Perfil | Evidencia real actual | Límite y siguiente comprobación |
| --- | --- | --- |
| Servicios AOSP de Markor | Parser original lee XML y falla por IPermissionManager.getSplitPermissions nulo | No arranca Application; fuente del ensayo JNI sigue pendiente y separada del commit de revisión. Comparar cierre de servicios en A/B. |
| Proveedores de documentos | REA: DocumentFile referido desde NewFileDialog/otros componentes; TreeDocumentFile.createFile llama DocumentsContract/ContentResolver | Estático: no demuestra guardado, grant o revocación. Probar URI/provider real; nube añade autenticación/backend. |
| Bibliotecas/media VLC | REA: play() espera superficies y llama nativePlay; ELF Bionic x86_64 inventariado previamente | No carga/reproducción probada, backend de codec/audio preciso pendiente. Comparar binarios originales y adaptación Linux. |
| GMS, autenticación/push/mapas | No prefijos GMS/Firebase en las tablas DEX examinadas de las tres APK | Búsqueda acotada, no ausencia garantizada de carga dinámica. Falta APK real que ejerza cada función; microG no evaluado en ejecución. |
| Integridad/billing | Sin APK/versión/cuenta/flujo fijados | Servicios y validación remotos; certificación/hardware según política. No tokens/veredictos/compras ficticios. |
| DRM | MediaDrm aparece como tipo en Markor/Calculator; REA no traza clases SDK externas ausentes en la APK | No atribuir reproducción Widevine a esas apps. Faltan ruta exacta y APK/contenido/condiciones de licencia. ClearKey es otra prueba, no sustituto de DRM comercial. |
| ARM-only, WebView/splits | Sin flujo completo representativo | Casos requeridos, no exclusiones definitivas; selección de artefactos y prueba pendientes. |

Los tres recorridos originales siguen abiertos; las nueve etapas sobre A16 son no probadas. La selección
de Markor local es una primera vertical, no reducción del objetivo a archivos
locales ni una acreditación de todos sus proveedores. El [contrato](CONTRATO-APK.md)
y [la arquitectura](ARQUITECTURA.md) fijan aceptación y alternativas.

### Markor · firma original verificada (API36)

[Verificación](../reports/android16-markor-original-signature/verification.json): apksig de la revisión AOSP bloqueada verifica firma v2 del APK intacto; copia negativa alterada falla por digest. Certificado y hashes registrados. REA MCP sólo aporta estructura declarada, no verifica criptografía. Las nueve etapas funcionales permanecen no probadas: esto no es instalación por PackageManager ni lanzamiento.
