# Roadmap A · compatibilidad APK mínima sobre Linux

Objetivo aclarado por el usuario: estudiar AOSP y reproducir o reutilizar el mínimo
necesario para ejecutar APK de forma estable sobre Linux, dentro de nuestra sesión
Rust/Smithay. No se persigue arrancar un sistema Android completo ni envolver
Waydroid. El éxito se mide por ejecución real de aplicaciones, no por boot Android.

| Etapa | Trabajo concreto | Puerta de salida | Estado |
| --- | --- | --- | --- |
| A0 · superficie real | APK propia pequeña, inventario DEX/recursos/JNI y pruebas funcionales; revisar contrato según esas necesidades | APK y fuentes fijadas, APIs realmente usadas identificadas, pruebas reproducibles | Verificado para la fixture: inventario, recursos, firmas y comportamiento; contrato experimental en CONTRATO-APK.md |
| A1 · ejecución DEX | Estudiar ART/libcore en modo host y alternativas; prototipo de ejecución sobre Linux sin sistema Android | Código DEX de la APK ejecutado con salida verificable, sin Waydroid ni arranque Android | Verificado para la APK propia: ART ejecuta onCreate/onClick y conserva preferencias entre procesos; sin UI todavía |
| A2 · primera interfaz | Subconjunto medido de Activity, ciclo de vida, recursos, View/texto/botón y entrada; puente hacia Wayland/Rust | APK propia sin modificar abre ventana, responde a entrada, guarda estado y se cierra correctamente | Verificado para la fixture: DRM/Pixman 720p, uinput→Wayland, cierre y reapertura 2→3; framework aún propio |
| A3 · servicios mínimos | JNI/ABI/Bionic donde sean necesarios, gráficos, audio, red, archivos y permisos según APK de prueba | Pruebas por API/servicio, errores explícitos en funciones ausentes y recuperación | Pendiente |
| A4 · compatibilidad y estabilidad | APK reales por ABI/API, reflexión, WebView y demás dependencias descubiertas; ampliar la capa con evidencia | Matriz por aplicación, pruebas prolongadas, reinicios y mediciones; fallos y cobertura registrados | Pendiente |
| A5 · distribución | Runtime y servicio anfitrión propios, paquetes, actualizaciones, migración de datos e integración TV | Instalación limpia sin Waydroid ni sistema Android completo, apps verificadas, actualización y rollback | Pendiente |

## Próximo experimento

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
