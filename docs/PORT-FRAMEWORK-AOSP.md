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
