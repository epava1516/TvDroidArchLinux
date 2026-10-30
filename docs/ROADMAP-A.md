# Roadmap A · compatibilidad APK mínima sobre Linux

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

## Prioridad vigente

Revisar arquitectura completa y reutilización AOSP antes de añadir dependencias
por fallos aislados. Definir matriz de APK reales y recorridos funcionales
completos. [ESTADO.md](ESTADO.md) es el punto de entrada; [EVIDENCIAS.md](EVIDENCIAS.md)
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
  Antes: coherencia de bootclasspath y aislamiento/identidad, bootstrap original
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
