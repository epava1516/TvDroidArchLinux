# Port selectivo del framework original a Linux

La dirección solicitada es reutilizar la implementación original de las API de
AOSP, adaptando sus dependencias a Linux y Wayland. ART ya está ejecutándose en
Linux. Las clases android.* actuales del prototipo son propias y no deben
presentarse como framework AOSP portado. La prueba visual del contador permanece
como regresión durante la sustitución.

## Base de estudio fijada

Se ha fijado frameworks/base de Android 13 en la revisión
bff944d05cd47d2b3b713565d3f00d512840d282, coherente con la rama del ART host
estudiado. El inventario inicial enumera 17 archivos, 3 148 358 bytes,
con tamaño y SHA-256. Se descargan únicamente esos archivos a caché, sin árbol
Android completo. reports/aosp-framework-study/dependencies.json registra imports,
declaraciones native y referencias léxicas entre tipos del mismo paquete.

```bash
python tools/apk/study_framework.py --cache "$HOME/.cache/archtv/aosp-framework-study/pinned" --output dist/apk/estudio-framework-nuevo --fetch
```

El inventario es léxico, no un cierre transitivo ni prueba de compilación. Detecta
61 declaraciones native en los archivos Java seleccionados: seis en MessageQueue,
54 en AssetManager y una en Activity. Que View no declare métodos native propios
no elimina sus dependencias gráficas/JNI a través de otras clases.

## Fronteras concretas

| Conjunto original | Dependencia observada | Adaptación o estudio siguiente |
| --- | --- | --- |
| Looper, Handler, Message, MessageQueue | Referencias recíprocas; SystemClock, identidad Binder, ThreadLocalWorkSource, trazas, Parcel/Bundle y seis métodos native de cola | Compilar el conjunto y sus dependencias reales; portar espera/despertar/FD a Linux conservando ordenación y despacho Java originales |
| AssetManager, Resources, ResourcesImpl | 54 puntos native de AssetManager; android_util_AssetManager.cpp usa androidfw y JNI | Portar recursos originales y dependencias host; verificar configuraciones, strings, XML y errores contra AOSP |
| View, ViewGroup, ViewRootImpl | ViewRootImpl importa 210 tipos, incluidos ventanas, entrada y superficies | Determinar la frontera de ventanas/gráficos; conservar lógica original de vistas y conectar la presentación con Wayland |
| Activity, ContextImpl y wrappers | Activity importa 152 tipos y ContextImpl 98; servicios, PhoneWindow, recursos y clases internas | Adaptar lanzamiento, contexto y servicios requeridos; ejecutar el ciclo original con la APK de regresión |
| SharedPreferencesImpl | XML, FileUtils, Os/StructStat, Looper, histogramas y XmlUtils | Portar con persistencia y notificaciones reales; no sustituir sólo la interfaz y llamar a eso port de preferencias |

Fuentes originales principales:
[MessageQueue.java](https://android.googlesource.com/platform/frameworks/base/+/bff944d05cd47d2b3b713565d3f00d512840d282/core/java/android/os/MessageQueue.java),
[JNI de MessageQueue](https://android.googlesource.com/platform/frameworks/base/+/bff944d05cd47d2b3b713565d3f00d512840d282/core/jni/android_os_MessageQueue.cpp),
[AssetManager.java](https://android.googlesource.com/platform/frameworks/base/+/bff944d05cd47d2b3b713565d3f00d512840d282/core/java/android/content/res/AssetManager.java),
[ViewRootImpl.java](https://android.googlesource.com/platform/frameworks/base/+/bff944d05cd47d2b3b713565d3f00d512840d282/core/java/android/view/ViewRootImpl.java),
[Activity.java](https://android.googlesource.com/platform/frameworks/base/+/bff944d05cd47d2b3b713565d3f00d512840d282/core/java/android/app/Activity.java).

## Secuencia y pruebas del port

1. **Fuentes y cierre de compilación:** registrar fuentes originales, licencias,
   parches y adaptadores por separado. Compilar el conjunto Looper/Handler/Message/
   MessageQueue para descubrir dependencias adicionales; imports no bastan.
2. **Cola original sobre Linux:** implementar el enlace JNI necesario con espera,
   despertar y descriptores reales. Probar FIFO, mensajes diferidos, cancelación,
   hilos cruzados, idle handlers, barreras, quit y quitSafely. No reemplazar la
   cola original por un simulador que sólo pase el contador.
3. **Recursos originales:** estudiar y compilar androidfw/AssetManager con sus
   dependencias; probar recursos y errores de tablas reales antes de sustituir
   el lector propio. Registrar cada operación aún no soportada.
4. **Vistas y ventanas originales:** portar el conjunto necesario de View/Window,
   gráficos y ciclo de vida; adaptar la frontera de presentación a Smithay/Wayland.
   La ventana anterior basada en JSON sirve de comparación, no acredita este port.
5. **Sustitución y ampliación:** volver a ejecutar la APK original, entrada y
   persistencia; ampliar a otras aplicaciones, servicios, ABI/JNI y errores.
   Después medir consumo/estabilidad y completar instalación, actualización y
   rollback de A3–A5 y las puertas generales del proyecto.

No se necesita arrancar un sistema Android completo como criterio del port.
Tampoco se presupone que se puedan eliminar todos sus servicios sin adaptar
contratos: cada dependencia debe resolverse, portarse o rechazarse explícitamente.
## Primer conjunto original compilado

Looper, Handler, Message y MessageQueue ya compilan sin modificar sus fuentes,
contra una referencia interna Android 13 y dos declaraciones auxiliares de
compilación. D8 genera un DEX que excluye la referencia completa y esas
declaraciones. En ART, Looper.prepare entra en el constructor original de
MessageQueue y se detiene en nativeInit con UnsatisfiedLinkError. El método
privado getInt$ de FileDescriptor se comprobó en el ART real por reflexión.

Ver runtime/aosp/README.md y reports/aosp-queue-compile/. No funciona aún la cola;
el siguiente paso es su JNI Linux y las dependencias de ejecución posteriores.
El cierre de compilación no prueba que ya se haya resuelto todo ese conjunto,
ni sustituye las API propias que sigue usando el contador.

## JNI Linux verificado

El enlace Rust de los seis métodos native de MessageQueue ya pasa creación,
espera, despertar, FD con listener Java original y destrucción en ART. Se añadieron
cuatro utilidades originales sin modificarlas: el manifiesto contiene ahora 21
archivos. Falta el despacho con Handler/Looper.loop, cuya prueba encuentra ahora
Parcelable ausente. Ver AOSP-JNI-LINUX.md y reports/aosp-queue-jni/.

## Primer despacho original

El conjunto se amplió a 19 fuentes originales y ya ejecuta Handler.post/Looper.loop
con relojes e identidad local Linux. Pasan las pruebas de semántica descritas en
AOSP-HANDLER-LINUX.md; todavía no se integró este bucle en el contador ni se portó
Binder IPC, Activity/View o recursos originales. La documentación conserva el
timeout inicial sin atribuir su causa y mantiene las puertas de estabilidad abiertas.

## Integración en la APK

El contador ya usa el principal y Handler originales para sus callbacks. La
regresión de entrada/persistencia y las capturas DRM pasan, incluida contrapresión
de comandos y recuperación tras error. Ver APK-LOOPER-AOSP.md. Esto integra el
bucle original; no acredita Activity/View/recursos originales ni Binder IPC.

## Recursos nativos originales en Linux

La construcción host estática de libandroidfw ya resuelve los tres textos de la
APK original y pasa la variante con el mismo DEX y los casos de recursos
ausentes/truncados. Ver AOSP-RECURSOS-LINUX.md y reports/aosp-androidfw-build/.
El contador todavía utiliza su proveedor Java reducido: falta conectar los
recursos originales mediante JNI. Este hito no cierra el port de Activity/View.

El puente JNI ya ejecuta también AssetManager.getResourceText y ApkAssets/
StringBlock originales en ART. El constructor interno de la prueba evita la
inicialización de recursos del sistema aún pendiente; no se ha conectado todavía
el proveedor de recursos del contador. Ver reports/aosp-resources-jni/.

El conjunto ampliado ya ejecuta el constructor público de Resources y su lectura
de cadenas/configuración: AOSP-RESOURCES-PUBLICO.md documenta las 48 fuentes
originales y la excepción de cuatro clases generadas reutilizadas como bytecode.
No se carga la referencia completa. Sigue pendiente integrarlo en el contador
y cerrar la inicialización de recursos de sistema y el port de Activity/View.

El siguiente conjunto incorpora Context, ContextWrapper y Application originales.
El Context reducido se retiró y los hooks de Linux quedan separados de los
métodos originales. CONTEXTO-AOSP-LINUX.md documenta soporte real, rechazos y
pendientes de ContextImpl/LoadedApk y servicios.

## Compilación inicial de vistas

--with-views compila View/ViewGroup/ContextThemeWrapper originales sobre el
conjunto anterior. La carga real en ART sólo completa ContextThemeWrapper;
View/ViewGroup siguen bloqueadas. AOSP-VISTAS-LINUX.md y
reports/aosp-views-linkage/ registran el diagnóstico y las dependencias estáticas.
Todavía no hay objeto View original ni sustitución de la interfaz del prototipo.


El conjunto ampliado de 67 fuentes originales ya inicializa View, ViewGroup y
ContextThemeWrapper en ART sin la referencia completa. Pasa la prueba de 1.024
combinaciones de StateSet y los helpers estáticos de medida. Un binding mínimo
R.styleable se genera desde XML AOSP y se contrasta durante el build; no sustituye
los recursos de sistema. Ver reports/aosp-views-initialization/. Construcción de
objetos, dibujo e integración en las APK siguen pendientes.


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

El estudio fijado de cuatro fuentes HWUI identifica la variante original host de
libhwui como siguiente base de construcción. AOSP-RENDERNODE-NATIVO.md detalla
ownership, dependencias Skia/Minikin y la separación entre crear RenderNode y
presentar píxeles. Ese primer estudio aún no incluía compilación ni ejecución
gráfica nativa nueva.

La prueba posterior ya compila 14 unidades nativas HWUI originales, incluido el
JNI RenderNode, con cabeceras Skia/Linux fijadas y sin modificar sus fuentes.
Los informes aosp-hwui-host-objects conservan comandos, hashes y símbolos sin
resolver. El enlace completo, la convención CriticalNative host/ART y la
ejecución de RenderNode permanecen pendientes; no se acredita dibujo original.
