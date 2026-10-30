# Contrato experimental del runtime APK

Este contrato describe el prototipo ejecutado, separado del antiguo proveedor
Waydroid. Su primer consumidor será un cliente Wayland en Rust. Todavía no es una
ABI pública estable ni un mecanismo de aislamiento para APK no confiables.

## Proceso y entradas

El anfitrión inicia ART host con el DEX de runtime y la APK original en el
classpath. Main recibe ruta de APK, nombre cualificado de Activity y directorio
de datos. Se selecciona la Activity explícitamente; aún no se analiza el manifiesto
binario para descubrir su punto de entrada. No se inicia Zygote ni system_server.

AppEnvironment carga resources.arsc y preferencias. ART resuelve MainActivity de
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

Recursos no soportados y APIs ausentes deben fallar explícitamente. El lector
actual limita resources.arsc a 16 MiB, pools a 65536 strings y referencias a 16
saltos. Sigue el formato de
[ResourceTypes.h de AOSP](https://android.googlesource.com/platform/frameworks/base/+/android-13.0.0_r3/libs/androidfw/include/androidfw/ResourceTypes.h),
con un subconjunto propio descrito en runtime/apk/README.md.

## Evidencia y aceptación

reports/a1-counter-headless conserva la construcción, comandos, hashes y salidas
de la APK original y de las variantes separadas de prueba. El comprobador verifica
que el runtime no contiene clases de la fixture. El criterio de A1 se cumple para
esa APK al ejecutar DEX y observar sus callbacks y persistencia. A2 permanece
abierto hasta probar ventana Wayland, entrada real, cierre y reapertura. No se
extrapola ese resultado al resto de APK ni se cierra estabilidad/distribución.
