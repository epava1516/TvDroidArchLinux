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
