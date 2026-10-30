# Contrato vigente de ejecución APK

Revisión BASE-AOSP-1 · 2026-10-30. El objetivo es ejecutar APK completas sin
modificar sobre Linux, con compositor y shell Rust/Smithay, sin Waydroid ni un
Android completo arrancado detrás de la interfaz. La compatibilidad amplia,
aislamiento, estabilidad, ligereza, instalación y actualización son requisitos;
ninguna ruta técnica queda aceptada por defecto. Este contrato sustituye las
reglas del prototipo A1/A2 conservadas más abajo como historia.

## Alcance y frontera con Android completo

Se permite reutilizar código, bibliotecas y servicios AOSP originales, incluso
procesos Bionic x86_64 supervisados por Linux. Un servicio individual no equivale
a arrancar Android: debe declarar versión, proceso/ABI, dependencias transitivas,
IPC, permisos, identidad, archivos/dispositivos, inicio/cierre, coste y fallos.
Hay que demostrar su cierre mínimo; no basta renombrar un sistema Android como
«capa». El supervisor, sesión, ventanas y política TV pertenecen a nuestro Linux.

No se acepta boot de una imagen/kernel Android, Android init como sistema gestor,
ni iniciar la cadena estándar init→Zygote→system_server→SystemUI/SurfaceFlinger
para envolverla con Smithay. Tampoco un contenedor/VM Android completo oculto.
Extraer componentes de una imagen no es arrancarla. Namespaces/chroot de una
selección de componentes no son automáticamente Android completo, pero tampoco
prueban aislamiento: hay que inventariar lo realmente ejecutado.

No se prohíbe por nombre cada componente de esa cadena: si reutilizar un servicio,
lanzador o código de Zygote exige activar el conjunto completo, registrar el
conflicto antes de cambiar el alcance. Un system_server monolítico con servicios
sin cierre verificado no satisface esta restricción. No se reduce compatibilidad
silenciosamente para evitar esa tensión. No se instalará ni arrancará otro Android
para la revisión de base.

## Requisitos y evidencia de aceptación

| ID | Requisito | Evidencia necesaria |
| --- | --- | --- |
| C1 | APK originales completas | SHA-256/versiones, firma criptográfica y procedencia/política de confianza; no parchear APK ni sustituir su código por una réplica. Splits y bibliotecas dinámicas se registran explícitamente. |
| C2 | Base reproducible | Build/revisión/ABI de ART, libcore, Bionic/linker, framework/APEX/JNI/recursos y servicios, classpath y namespaces; hashes/licencias. Stubs SDK sólo compilan: no cuentan como implementación ejecutable. |
| C3 | Aplicación real completa | Las seis etapas de la matriz: lanzamiento por manifiesto/alias, interfaz propia de la APK, entrada real, persistencia, servicios y cierre/reapertura. Fixtures y pasos de bootstrap son regresiones parciales. |
| C4 | Aislamiento e identidad | Separación real por APK, permisos/URI/FD/Binder y datos, IPC autenticado, límites de procesos/memoria/red, lectura de código y recursos protegida. Probar accesos cruzados, denegación y caída; UID declarado no sustituye credenciales reales. |
| C5 | Estabilidad y ligereza | Mantener puertas H7: latencias, CPU/PSS y presupuestos, frame pacing, soak, ciclos y recuperación. Contabilizar todos los servicios compartidos y por app, además del shell; presupuesto global del runtime aún por medir/decidir. |
| C6 | Instalación/actualización | Dependencias/versiones/licencias fijadas; instalación limpia, migración de datos, actualización atómica, rollback y recuperación H8/H9. Una caché SDK del laboratorio no es un paquete distribuible aceptado. |
| C7 | Fallos honestos y servicios externos | Por función: contrato usado, implementación candidata, ABI e ISA, resultado real y límites. No devolver certificados, tokens, capacidades DRM o éxito de API ficticios. Ausencias/denegaciones se observan como tales. |

La matriz canónica es [COMPATIBILIDAD-APK.md](COMPATIBILIDAD-APK.md) y su JSON
vinculado. Marcar una etapa como verificada requiere artefacto/commit, comandos,
resultado observable y limitaciones. Compilar, enlazar Activity, inicializar
ContextImpl o registrar JNI no cumplen C3. API de servicio, ABI Bionic/JNI e ISA
son ejes separados; x86_64 oficial no ejecuta automáticamente bibliotecas ARM.

## Servicios externos y propietarios

El catálogo de dependencias de la matriz distingue código reutilizable, binarios
originales candidatos, adaptación Linux y servicios remotos. Antes de implementar
una compatibilidad nueva se evalúan alternativas existentes (p. ej. microG,
libhybris o las bibliotecas multimedia originales), con versión y prueba de la
función concreta. No se consideran reemplazos generales por su nombre.

Google Play Services/GMS, autenticación/push/mapas/pagos e integridad, proveedores
de documentos/multimedia, codecs/HAL y DRM tienen pruebas separadas por aplicación.
Un proveedor local no acredita acceso a una nube autenticada; reproducir un
fichero libre no acredita Widevine. Licencias, servidor de licencias, cuenta,
provisioning, certificación, TEE/hardware o backend fuera del control local deben
quedar explícitos. No se simulan atestaciones ni se extraen secretos. Sin APK o
cuenta de prueba disponible, la cobertura queda pendiente, no aprobada.

## Experimento vertical para decidir base

Misma Markor 2026.10.0 intacta y mismo recorrido en ambas rutas: seleccionar su
Activity original por manifiesto, crear/editar una nota local con contenido de
control, recibir teclado/mando a través de Smithay, guardar, usar la ruta de
archivo/proveedor realmente elegida, cerrar sin huérfanos y reabrir verificando
los bytes guardados. Observar callbacks, permisos y fallos; no sustituir la UI.
La ruta SAF requiere probar grants y revocación del proveedor; el recorrido local
inicial no cierra nube/SAF/otras funciones de Markor.

A: ART host/glibc con subsistemas originales adaptados. B: runtime nativo
Bionic/AOSP x86_64 coherente en procesos Linux con fronteras Linux explícitas.
C: combinación sólo con IPC/ABI/versiones justificadas y pruebas de cada frontera.
El orden y puertas de decisión están en [ROADMAP-A.md](ROADMAP-A.md); la elección
final exige recorrido real, cierre de dependencias y costes medidos. Los ensayos
preparatorios no rebajan ese criterio. El soporte de API 33 del laboratorio no
se presenta como cobertura de todas las versiones Android ni como base segura
actualizada para distribución.

# Historia del prototipo A1/A2 · alcance limitado

Este contrato describe el prototipo ejecutado, separado del antiguo proveedor
Waydroid. Su primer consumidor será un cliente Wayland en Rust. Todavía no es una
ABI pública estable ni un mecanismo de aislamiento para APK no confiables.

## Proceso y entradas

El anfitrión inicia ART host con el DEX de runtime y la APK original en el
classpath. Main recibe ruta de APK, nombre cualificado de Activity y directorio
de datos. Se selecciona la Activity explícitamente; aún no se analiza el manifiesto
binario para descubrir su punto de entrada. No se inicia Zygote ni system_server.

AppEnvironment carga recursos mediante AssetManager/ApkAssets originales y mantiene
las preferencias del subconjunto propio. ART resuelve MainActivity de
la APK como subclase de nuestra Activity e invoca su constructor y onCreate.
La secuencia anfitriona es onCreate(null), onStart, onResume; al cerrar se llama
onPause, onStop, onDestroy. Estas transiciones se inspiran en el
[ciclo de vida Android](https://developer.android.com/guide/components/activities/activity-lifecycle);
no implementan todas sus condiciones, callbacks ni integración con ventanas.

## Canal de prueba

Entrada estándar: comandos UTF-8 terminados en salto de línea, máximo 4096 caracteres.

| Comando | Efecto |
| --- | --- |
| activate | performClick sobre la View con foco que pertenece al árbol; llama al listener real de la APK |
| dump | Emite el árbol actual sin modificar la aplicación |
| quit o EOF entre comandos | Cierra la Activity y libera el bloqueo de datos |

Salida estándar: una línea JSON por evento. ready y updated incluyen root con
class, focused, padding y, según el nodo, text/text_size, orientation y children.
closed indica que terminó la secuencia de cierre. Los errores y diagnósticos ART
van a stderr; una excepción no controlada termina con código distinto de cero.
No se captura System.out escrito por la propia APK, por lo que este canal aún
debe separarse antes de aceptar aplicaciones arbitrarias. El formato experimental
no tiene negociación de versión y no debe exponerse como protocolo estable.

El cliente futuro representará ese árbol y enviará activaciones desde eventos
reales de teclado/mando. Ningún texto o comportamiento específico del contador
debe introducirse en ese cliente. Primero habrá que añadir transporte separado,
límites de árbol/mensajes y supervisión de procesos para aplicaciones más amplias.

## Datos y fallos

El directorio de datos se crea con modo 0700. Un bloqueo exclusivo permanece
durante el proceso; otro propietario se rechaza. Las preferencias enteras se
guardan en archivos 0600 mediante temporal, sync y sustitución atómica. commit
devuelve éxito de persistencia y actualiza memoria; la API de referencia distingue
el resultado de la escritura síncrona en
[SharedPreferences.Editor](https://developer.android.com/reference/android/content/SharedPreferences.Editor#commit()).
No se ha probado durabilidad ante pérdida de energía. Lecturas corruptas fallan
sin sobrescribir datos. Los permisos Unix no sustituyen una política de acceso
entre APK: actualmente comparten el usuario del laboratorio.

Recursos no soportados y APIs ausentes deben fallar explícitamente. El adaptador
actual limita resources.arsc a 16 MiB y delega el análisis y las referencias en
libandroidfw original. El parser propio anterior se ha retirado. Todavía no hay
recursos de sistema, constructor público completo ni estilos; sólo están
probadas las cadenas de la fixture. Ver AOSP-RECURSOS-LINUX.md.

## Evidencia y aceptación

reports/a1-counter-headless conserva la construcción, comandos, hashes y salidas
de la APK original y de las variantes separadas de prueba. El comprobador verifica
que el runtime no contiene clases de la fixture. El criterio de A1 se cumple para
esa APK al ejecutar DEX y observar sus callbacks y persistencia. Ese primer ensayo dejó A2
abierto hasta las regresiones gráficas posteriores descritas a continuación. No se
extrapola ese resultado al resto de APK ni se cierra estabilidad/distribución.

## Integración actual del principal AOSP

El contador ya usa el Looper principal y Handler originales. El lector publica
comandos con contrapresión de 16 pendientes y todos los callbacks UI se ejecutan
en main. La librería Rust se carga explícitamente; no hay fallback al bucle anterior.
El cierre del anfitrión conserva la prohibición original de quit del principal y
libera la cola por su método dispose. Ver APK-LOOPER-AOSP.md. La regresión gráfica
actual, incluido cierre/reapertura, está en reports/aosp-main-ui-wayland/; A2 está
verificado para esta fixture, mientras el resto del framework sigue pendiente.

## Métricas de ventana

El protocolo experimental añade display:[ancho,alto] a ready/updated y el comando
configure ANCHO ALTO. Deben reconstruirse juntos DEX y cliente Rust. Los cambios
se aplican en el Handler UI y actualizan Resources original; no acreditan todavía
el ciclo completo de configuración de Activity/View. Ver AOSP-METRICAS-WAYLAND.md.
