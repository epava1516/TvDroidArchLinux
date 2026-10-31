# Contrato vigente · AOSP Android 16 QPR2

Versión contractual: A16-QPR2-1 · 2026-10-30. Instrucción vigente del usuario;
reemplaza las elecciones de base y restricciones gráficas de BASE-AOSP-1.
La verificación de versión/revisiones, decisiones de implementación y evidencia
están en [ARQUITECTURA.md](ARQUITECTURA.md), [ROADMAP-A.md](ROADMAP-A.md),
[ESTADO.md](ESTADO.md) y [COMPATIBILIDAD-APK.md](COMPATIBILIDAD-APK.md).
El contenido siguiente conserva el alcance completo del contrato recibido.

## OBJETIVO

Ejecutar APK completas sin modificar sobre nuestro Linux, integrado con nuestro compositor Rust/Smithay, sin Waydroid ni arrancar una distribución o imagen Android completa.

La meta es compatibilidad amplia con aplicaciones arbitrarias, incluidas Android TV: una plataforma general, sin seleccionar únicamente aplicaciones fáciles ni mantener adaptaciones particulares por APK como estrategia.

No prometas compatibilidad universal. Cualquier límite debe quedar identificado, demostrado y documentado, sin reducir silenciosamente el objetivo.

## PRINCIPIO DE IMPLEMENTACIÓN

Prioriza reutilizar subsistemas originales AOSP lo más completos y coherentes posible para reducir código propio, esfuerzo de estudio y divergencias de comportamiento.

“Fragmentos necesarios” significa unidades funcionales con sus dependencias reales, no clases o métodos aislados. Conserva un subsistema grande cuando dividirlo suponga más trabajo o menor compatibilidad.

Cuando los componentes originales puedan ejecutarse directamente sobre Linux con Bionic, consérvalos. No los portes a glibc por defecto.

Concentra los cambios en las fronteras con Linux y Smithay. Modifica el interior de los componentes originales únicamente ante una necesidad demostrada y registra cada desviación.

No uses stubs, respuestas ficticias o éxitos simulados para aparentar compatibilidad. Las funciones ausentes deben producir resultados explícitos y trazables.

## 1. PROTEGER EL TRABAJO EXISTENTE

Antes de modificar:

- Guarda un checkpoint del estado real: HEAD, rama, remotos, cambios pendientes, archivos nuevos, procesos y handles relevantes, pruebas, evidencias y siguiente acción.
- Separa el trabajo propio del pendiente o ajeno. No descartes, mezcles ni incorpores cambios sin comprobarlos.
- Conserva los experimentos anteriores como evidencia con alcance y limitaciones.
- Mantén el compositor, instalación, herramientas y pruebas que sigan siendo útiles.
- Desarrolla la nueva base del runtime de forma aislada y comparable. Sustituye la anterior cuando existan resultados que lo justifiquen.

No reinicies la VM ni el cliente como parte de este contrato.

## 2. BASE AOSP

Adopta Android 16 QPR2 como base inicial de ingeniería, con x86_64 como primera arquitectura de ejecución y diseño portable a ARM64.

Comprueba en fuentes oficiales la correspondencia exacta entre versión, rama, etiqueta y artefactos. Usa android-16.0.0_r4 como referencia inicial a verificar; fija después un manifiesto con revisiones exactas de todos los repositorios y registra su procedencia.

No confundas una etiqueta reproducible con una base de seguridad actualizada. Identifica e incorpora las correcciones necesarias, con pruebas, antes de distribuir.

Conserva una combinación coherente de Bionic, enlazador, ART, libcore, framework, recursos, JNI, módulos APEX y servicios. Documenta configuración, bootclasspath, classloaders, namespaces del enlazador y artefactos generados.

No mezcles builds o versiones sin justificar y probar sus fronteras. No uses stubs del SDK como implementaciones ejecutables del framework.

Distingue AOSP oficial, Cuttlefish/Android Emulator y el proyecto independiente Android-x86. Extraer artefactos oficiales no implica arrancar esos sistemas.

## 3. ARQUITECTURA DE EJECUCIÓN

La vía principal será conservar el entorno nativo Bionic/AOSP sobre nuestro kernel Linux, sin pasar por glibc para ejecutar el código Android.

Los procesos anfitriones podrán seguir utilizando glibc. Cualquier comunicación o intercambio entre entornos tendrá fronteras explícitas de procesos, ABI, memoria, propiedad de objetos, descriptores e identidad.

Conserva ART host/glibc como referencia experimental cuando sea útil. Una solución híbrida solo se aceptará si sus fronteras están justificadas y verificadas.

Evalúa subsistemas completos antes de reimplementar sus funciones. Identifica qué puede ejecutarse directamente, qué necesita configuración, qué requiere adaptación y qué introduce dependencias adicionales.

No presupongas que los servicios pueden separarse fácilmente de system_server o de otros componentes.

## 4. SIGNIFICADO DE “SIN ANDROID COMPLETO”

El anfitrión Linux conservará el control del arranque, supervisión, dispositivos, escritorio y compositor.

Se permite reutilizar procesos y servicios originales AOSP necesarios para las aplicaciones. Su mera presencia no equivale automáticamente a arrancar Android completo.

No introduzcas una VM, una imagen Android arrancada, Waydroid o un sistema Android completo oculto bajo nuestra interfaz.

Los namespaces u otros mecanismos de aislamiento deberán describirse por su función real; no deben utilizarse para ocultar un cambio de arquitectura.

Si la clausura de dependencias exige un entorno que entre en conflicto con esta restricción, presenta el conflicto con evidencia antes de cambiar el alcance.

## 5. COMPORTAMIENTO Y SERVICIOS

Preserva el comportamiento de los subsistemas, no solo sus firmas:

- Instalación, paquetes, firmas y resolución de componentes.
- Actividades, ventanas, ciclo de vida y recuperación de procesos.
- Binder, identidad del llamante, permisos y comunicación entre aplicaciones.
- Recursos, almacenamiento, proveedores de contenido e intents.
- Servicios, notificaciones, tareas programadas y segundo plano.
- Callbacks, concurrencia, errores y persistencia.

Determina sus dependencias mediante fuentes originales y pruebas. No avances mediante sustituciones vacías de servicios que únicamente permitan superar el siguiente fallo.

6. GRÁFICOS, ENTRADA Y MULTIMEDIA

Evalúa primero conservar la semántica gráfica original: WindowManager, Surface, BufferQueue, sincronización y componentes relacionados.

La primera alternativa a contrastar será conservar SurfaceFlinger y adaptar su salida hacia Wayland, con Smithay como compositor del anfitrión. Es una hipótesis de integración, no una solución previamente demostrada.

Compara alternativas solo cuando las pruebas revelen costes o limitaciones concretos. No reconstruyas todo el sistema gráfico por asumir que SurfaceFlinger es incompatible con Smithay.

Comprueba gráficos acelerados, buffers, fences, composición, ventanas, escalado, foco, teclado, ratón, táctil y mando/D-pad.

Incluye audio, vídeo, códecs, superficies de reproducción y sincronización audiovisual. Una captura estática o un menú visible no demuestra reproducción funcional.

Contempla las actividades y funciones específicas de Android TV. La semejanza visual con Fire TV no acredita compatibilidad con sus APK o servicios.

7. INSTALACIÓN, ACTUALIZACIÓN Y SEGURIDAD

Incluye:

- APK individuales y conjuntos de APK divididas.
- Verificación de firmas y coherencia del conjunto instalado.
- Selección de ABI y bibliotecas nativas.
- Instalación, actualización, migración de datos, desinstalación y recuperación.
- Versionado reproducible del runtime y reversión ante actualizaciones fallidas.

No confundas AAB, formato de publicación, con un APK directamente instalable.

Preserva aislamiento por aplicación, identidades, permisos efectivos y separación de datos. Verifica Binder y los requisitos reales del kernel de la base elegida.

Aplica límites de recursos y recuperación ante fallos. No dependas de ejecutar todas las aplicaciones bajo una identidad compartida o con privilegios generales.

Registra licencias, procedencia, modificaciones y mantenimiento de seguridad de los componentes reutilizados.

## 8. TRES EJES INDEPENDIENTES

Mantén separados en arquitectura, pruebas y resultados:

A. Compatibilidad de API, comportamiento y servicios.
B. Compatibilidad binaria Bionic/JNI y enlazado.
C. Compatibilidad de instrucciones y arquitecturas, incluyendo 32/64 bits.

Valida inicialmente APK sin código nativo y con bibliotecas x86_64. Investiga traducción ARM→x86_64 como línea independiente, sin usarla para posponer el diseño de sus fronteras.

Ejecutar bytecode con ART no demuestra compatibilidad JNI. Ejecutar una biblioteca x86_64 no demuestra soporte ARM. Compartir kernel Linux no demuestra compatibilidad del entorno Android.

Respeta los mecanismos de comportamiento según targetSdkVersion. Identifica las APK que requieran API posteriores a la base y planifica su evolución sin fingir soporte.

## 9. DEPENDENCIAS EXTERNAS Y PROPIETARIAS

Incluye Google Play Services, alternativas existentes como microG cuando correspondan, WebView, DRM, proveedores multimedia, servicios OEM y servicios remotos.

Para cada dependencia:

- Identifica el contrato realmente utilizado por la aplicación.
- Distingue implementación reutilizable, biblioteca original, adaptación local y servicio remoto.
- Evalúa soluciones existentes antes de desarrollar otra.
- Documenta autenticación, licencias, certificación, claves, hardware seguro y aceptación por servidores externos.
- Comprueba su funcionamiento o limitación con aplicaciones reales.

No presupongas que AOSP proporciona GMS, que una API local sustituye un backend o que comprender DRM proporciona claves o certificación.

Distingue aplicaciones ordinarias de aplicaciones privilegiadas o vinculadas a un fabricante. No modifiques las APK para eludir esas diferencias y contarlas como compatibles.

## 10. USO DE FUENTES Y REA

Comprueba que REA MCP está realmente disponible y funcional. No presentes su CLI como prueba de conexión MCP.

Para código abierto AOSP, estudia primero las fuentes originales de la revisión utilizada. Usa REA para inspeccionar artefactos compilados, APK, JNI, dependencias y divergencias respecto a esas fuentes, dentro de sus capacidades reales.

Procedimiento de diagnóstico:

1. Reproducir el fallo y conservar evidencia.
2. Identificar el contrato solicitado por la aplicación.
3. Contrastar fuentes y artefactos concretos.
4. Localizar la divergencia de nuestro entorno.
5. Corregir preferentemente el subsistema o su frontera.
6. Repetir el recorrido y añadir una regresión significativa.
7. Comprobar si la corrección beneficia a otras aplicaciones.

REA reduce incertidumbre; no proporciona automáticamente implementaciones, servicios, traducción de instrucciones o infraestructura externa.

Mantén separados análisis estático, hipótesis y resultados de ejecución. Si REA MCP no está disponible, registra la limitación y continúa solo el trabajo independiente que pueda sostenerse con otras evidencias.

## 11. VALIDACIÓN

Utiliza CDD y CTS de la versión correspondiente como referencias técnicas. Introduce pruebas pertinentes de CTS conforme la infraestructura permita ejecutarlas y registra también las no ejecutadas.

No presentes un subconjunto de CTS como certificación Android.

Mantén una matriz de APK reales, con versiones, hashes, procedencia, API, ABI, dependencias y recorridos reproducibles. Incluye progresivamente:

- Markor y almacenamiento/proveedores.
- Calculator y dependencias nativas.
- VLC y multimedia.
- Aplicaciones Android TV y navegación con mando.
- Aplicaciones con WebView, gráficos acelerados y servicios externos.

Las fixtures propias serán regresiones, no el criterio general de compatibilidad.

Para cada aplicación registra al menos: instalación, lanzamiento, interfaz, entrada, función principal, persistencia, servicios, cierre y reapertura.

Distingue aprobado, fallo demostrado, bloqueo externo y no probado. No conviertas “no probado” en un porcentaje de compatibilidad.

Cuando sea posible, compara el mismo recorrido con un dispositivo Android de referencia externo. No arranques otro sistema Android local sin autorización para ello.

## 12. HITOS Y PUERTAS DE DECISIÓN

Primero demuestra una base Bionic/ART coherente con sus dependencias y configuración originales.

Después completa el recorrido de Markor ya definido, incluyendo interfaz real, entrada, edición, persistencia y reapertura. La selección del primer caso no reduce el alcance general.

A continuación demuestra que la misma base permite avanzar en aplicaciones de categorías distintas sin reconstrucciones particulares por APK.

Compilar, cargar clases, resolver JNI, inicializar ContextImpl o mostrar un widget son hitos parciales. Ninguno cierra el runtime ni acredita una aplicación completa.

Mide RAM, CPU, arranque, latencia de entrada, estabilidad y consumo de recursos. Define presupuestos a partir de resultados y hardware documentado. No obtengas ligereza eliminando silenciosamente comportamiento necesario para las aplicaciones.

## 13. DOCUMENTACIÓN Y ENTREGA

Revisa y actualiza los documentos canónicos existentes de contrato, arquitectura, roadmap, estado, evidencias y matriz. No crees fuentes de verdad duplicadas.

Para cada decisión registra: alternativa elegida, motivo, evidencia, modificaciones propias, dependencia pendiente y prueba de aceptación.

Conserva los experimentos anteriores con su alcance histórico. Actualiza Graphify según AGENTS.md.

Guarda la revisión contractual y arquitectónica en un commit separado. Conserva los cambios ajenos o pendientes y no los incorpores accidentalmente. Haz commits y push de hitos comprobados conforme a la autorización existente.

Continúa autónomamente con la estrategia sustentada por las pruebas. Si la evidencia contradice una hipótesis, revisa la decisión de forma explícita; no alteres el objetivo ni declares compatibilidad por superar únicamente pruebas parciales.

## Ampliación vigente R6 · instrucción del 2026-10-31

Antes de implementar traducción ARM, evaluar Native Bridge original de AOSP y
traductores existentes, especialmente libndk_translation y Houdini, frente a
Android16 QPR2, JNI, bibliotecas invitadas, licencias y redistribución. QEMU
user-mode es una alternativa experimental y no un Native Bridge integrado.
No desarrollar un traductor propio sin demostrar primero la insuficiencia de
las opciones existentes. Mantener esta investigación separada del avance x86_64.
[Evaluación y puertas](TRADUCCION-ARM.md), sin aceptación ARM por estudio estático.

# Historia preservada · no establece requisitos vigentes

# Contrato anterior BASE-AOSP-1 · histórico

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
