# Matriz de aplicaciones reales

Fuente de los registros: [compatibility-matrix.json](../reports/arquitectura-apk-20261030/compatibility-matrix.json).
Contiene APK, versión/código, SHA-256, procedencia, SDK, bibliotecas nativas,
certificados declarados, Evidence IDs y seis resultados funcionales por app.
Las APK están intactas en caché local; no se recompilan ni se parchean.

| APK fijada | Perfil observado | Recorrido a verificar | Ejecución actual |
| --- | --- | --- | --- |
| Markor 2026.10.0, net.gsantner.markor | minSDK 21, target 35; no miembros lib/*.so en este APK | Crear/editar nota, entrada real, guardar, cerrar/reabrir | Lanzamiento, interfaz, entrada, persistencia, servicios y cierre: no ejecutados |
| Calculator 1.4.0, org.fossify.math | minSDK 26, target 36; AndroidX Path para arm64/armv7/x86/x86_64 | Alias de lanzador, 2+3, historial/preferencias, cierre/reapertura | Los seis pasos no ejecutados |
| VLC 3.7.1, org.videolan.vlc | minSDK 17, target 36; VLC/medialibrary/C++ x86_64 | Fichero local, audio/vídeo, volver al shell, cierre | Los seis pasos no ejecutados en el runtime propio; Waydroid anterior no cuenta |

REA MCP/JADX observa respectivamente 4.985/5.023/15.261 clases; estos inventarios
no prueban cobertura dinámica. El ensayo del framework enlaza clases Activity de
Markor y Calculator sin inicializarlas: no cambia los seis resultados not_run.
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

Los tres recorridos originales siguen abiertos en sus seis etapas. La selección
de Markor local es una primera vertical, no reducción del objetivo a archivos
locales ni una acreditación de todos sus proveedores. El [contrato](CONTRATO-APK.md)
y [la arquitectura](ARQUITECTURA.md) fijan aceptación y alternativas.
