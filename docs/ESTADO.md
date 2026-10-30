# Estado actual y punto de entrada

Actualizado: 30 de octubre de 2026. Esta cabecera es el estado vigente; el
historial inferior conserva experimentos y fronteras ya superadas. Git y los
artefactos enlazados prevalecen sobre cualquier resumen.

## Retomar en este orden

1. Leer [el checkpoint fechado](../reports/aosp-isolated-bootstrap/checkpoint.json)
   y contrastarlo con Git/procesos siguiendo [CONTINUIDAD.md](CONTINUIDAD.md).
2. Consultar [arquitectura y decisiones](ARQUITECTURA.md),
   [roadmap general](../ROADMAP.md) y [detalle APK](ROADMAP-A.md).
3. Consultar [el índice de evidencias](EVIDENCIAS.md) antes de atribuir un resultado.
4. Continuar el bootstrap original por conjuntos según [la revisión de arquitectura](ARQUITECTURA.md)
   y [la matriz real](COMPATIBILIDAD-APK.md). No volver a ampliar sustitutos Android por inercia.

## Objetivo y alcance real

Ejecutar APK completas sin modificar sobre Linux y compositor Rust/Smithay, sin
Waydroid ni arrancar un Android completo. Compatibilidad amplia, aislamiento,
estabilidad, ligereza, instalación y actualización siguen siendo requisitos.
Las fixtures, compilaciones y constructores no acreditan ese resultado.

| Clasificación | Estado comprobado y límites |
| --- | --- |
| Vigente | Compositor y shell Rust existen; pruebas H0–H5 limitadas a la VM y plataformas documentadas. H7–H9 siguen abiertos. |
| Experimental publicado | ART host ejecuta fixtures; recursos, cola y partes de contexto AOSP se reutilizan. Activity/widgets/vistas del contador siguen siendo propios. No hay compatibilidad general acreditada. |
| Experimental publicado | Registro local y layout/resize de View original probados en `b8ea156`; no dibujan la APK. Bootstrap aislado: UID 10000, Looper y ActivityThread originales; ContextImpl falla por framework modular incompleto antes de ejecutar Markor. |
| Herramientas verificadas | REA MCP 6.8.0 respondió a Codex y analizó estáticamente VLC 3.7.1 y una biblioteca ELF. La sesión de archivo se exportó y cerró. No es una prueba de ejecución de VLC en el runtime propio. |
| Histórico | H6 Waydroid, imágenes Android e ISO anteriores conservan evidencia; no son el backend ni la aceptación vigentes del runtime APK. |
| Desconocido/no verificado | Compatibilidad de aplicaciones reales en este runtime, aislamiento por APK, GPU del runtime, ARM, WebView, DRM/servicios propietarios, consumo y estabilidad prolongada. |

## Trabajo preservado y siguiente acción

Base del checkpoint vigente: `b8ea156`; el HEAD actual y origin se consultan con Git.
El snapshot distingue cambios propios del registro experimental y los logs
ajenos `reports/h9-uefi-boot/qemu.log` y `serial.log`. No se han descartado ni
incluido esos cambios de código en el desvío documental.

El reinicio afectó sólo a codex-remote.service, no a la VM. El checkpoint conserva
PIDs/handles observados y estados terminales; no presupone que sigan activos.
No se espera actualmente ningún build o prueba. Las autorizaciones ya concedidas
para pruebas, commits/push y trabajo autónomo siguen vigentes; no hay autorización
nueva para reiniciar la VM.

Siguiente acción concreta: obtener implementaciones originales y metadatos de un
bootclasspath modular coherente. El bundle R8 no basta para ContextImpl; el SDK
Connectivity consultado contiene stubs, que no se usarán como runtime. Después,
retomar el bootstrap aislado de Application y el recorrido completo de Markor.
[Resultado y límite actuales](../reports/aosp-isolated-bootstrap/result.json):
no se ejecutó código de Markor, ni onCreate ni su interfaz. La matriz continúa
sin recorridos funcionales completos. El aislamiento sólo tiene comprobaciones
parciales de namespace, no aceptación general de seguridad.

## Historial conservado (no es el estado vigente)

### Capa de compatibilidad APK propia sobre Linux

La dirección solicitada es estudiar AOSP para reutilizar o reproducir el mínimo
necesario para ejecutar APK de forma estable en Linux, sin Waydroid y sin arrancar
un sistema Android completo. Nuestro compositor y shell siguen siendo Rust/Smithay.
El desarrollo se organiza en [ROADMAP-A.md](ROADMAP-A.md).

## Qué se debe demostrar

Una APK propia, sin reescribirla como aplicación Linux, debe ejecutar su código,
resolver las APIs que usa, abrir una ventana en nuestro compositor, recibir entrada,
conservar estado y cerrar correctamente. Después se ampliará la compatibilidad
con APK reales y se medirán estabilidad, aislamiento y consumo.

Se investigarán por separado:

- DEX: ejecución y biblioteca de clases, estudiando ART/libcore y su posible uso host.
- Framework: subconjunto requerido de ciclo de vida, recursos, vistas y servicios.
- Gráficos/entrada: puente a Wayland y nuestra sesión Rust, con presentación real.
- JNI: ABI, bibliotecas nativas y compatibilidad Bionic cuando las APK lo requieran.
- Servicios: audio, red, almacenamiento y permisos incorporados según pruebas.

No se presupone que ART solo ejecute cualquier APK. La
[documentación de ART](https://source.android.com/docs/core/runtime) identifica
DEX como su formato de ejecución; la resolución de APIs y dependencias de la
aplicación constituye trabajo adicional de nuestra capa. Compartir el kernel
no convierte bibliotecas ARM en x86_64 ni garantiza compatibilidad de JNI.

## Primer estudio implementado

```bash
python tools/apk/apk_inventory.py ARCHIVO.apk INFORME.json
```

El analizador no instala ni ejecuta Android. Lee tablas DEX de versiones 035–040,
resta clases definidas en todos los DEX y registra referencias externas de plataforma,
propietarios de referencias de métodos y bibliotecas lib/ABI/*.so. Usa límites de
entrada y comprueba rangos básicos. El formato se basa en la
[especificación DEX](https://source.android.com/docs/core/runtime/dex-format).

El ensayo sobre VLC 3.7.1 x86_64 encuentra seis DEX, 1628 descriptores externos de
plataforma y cuatro bibliotecas nativas. Es una aplicación compleja de referencia,
no la APK elegida para el mínimo inicial. Ver reports/a0-apk-study/vlc-static.json.
Las referencias estáticas no indican qué código se ejecutará ni cubren reflexión,
JNI o carga dinámica. El informe no verifica firma, manifiesto, recursos o ELF,
no es un verificador DEX completo y no prueba compatibilidad ni ejecución.

## Alcance y recursos

No se iniciará una descarga del árbol AOSP completo por defecto. La cifra oficial
de 400 GB/64 GB corresponde al desarrollo de la plataforma completa y no se toma
como requisito demostrado de esta investigación selectiva. Los recursos de los
componentes elegidos deberán medirse. La VM dispone de unos 7,7 GiB y mantiene
un problema de estabilidad documentado en INCIDENTE-VM-20261030.md.

El contrato y adaptador Waydroid anteriores no se presentan como esta capa.
Se conserva el trabajo publicado como referencia histórica; su ampliación se ha
detenido. La aceptación de A no exige boot Android ni sys.boot_completed.

## APK propia preparada

La fixture fixtures/apk/counter ya está compilada y dispone de manifiesto, recursos,
fuentes y hashes. Su Activity contiene texto, botón y contador en preferencias.
No incorpora clases de framework Android ni bibliotecas JNI en el paquete.
La construcción no usó Android ni Waydroid. La ejecución DEX sobre Linux y el
puente de UI siguen pendientes. Ver reports/a0-fixture/ y el README de la fixture.

## ART host ejecuta DEX en Linux

Se descargó y verificó el conjunto ART 13 host publicado por R8, fijando revisión,
SHA-1 oficial y SHA-256. No se construyó ni arrancó Android. Una prueba DEX propia
pasó aritmética, recursión, interfaz, arrays, excepciones y reflexión básica en ART
con -Xint. La APK original del contador se encuentra en el classpath; su
MainActivity falla al resolver android.app.Activity, confirmado por el registro
de clases. No se ha ejecutado su ciclo de vida ni mostrado su interfaz.

El lanzador informa que falta framework/core.art y continúa sin imagen de clases
precompilada; la prueba semántica termina con código 0. La selección mínima,
compilación reproducible de ART y mediciones de consumo siguen pendientes. El
archivo del laboratorio no es el runtime final distribuible.
Ver ESTUDIO-ART-HOST.md y reports/a1-art-host/. A1/A2 no se dan por terminados.

## La APK propia ejecuta sus callbacks en Linux

El primer subconjunto de runtime/apk resuelve Activity, Context, View y preferencias
enteras. ART ejecuta el DEX de la APK original fijada: crea su árbol de texto/botón,
activa el listener 0→1→2 y, en otro proceso, recupera 2 y pasa a 3. No se recompilan
sus fuentes ni se incluyen clases org.archtv.probe en el DEX anfitrión. Los recursos
se leen de resources.arsc; una variante separada con DEX idéntico demuestra que el
texto cambia al cambiar el recurso.

El comprobador también verifica exclusión de un segundo proceso sobre datos
ocupados, liberación al cerrar, modos 0700/0600 y rechazo de recursos truncados y
preferencias corruptas. No hay ventana ni eventos Wayland todavía: A0/A1 están
verificados para esta fixture; A2 sigue en curso. La implementación no es una
capa Android completa ni aporta aún aislamiento o estabilidad prolongada.
Ver runtime/apk/README.md, CONTRATO-APK.md y reports/a1-counter-headless/.

## La APK tiene ventana Wayland y entrada real de la pila Linux

archtv-apk-host representa en Rust el árbol generado por la APK en ART. Dos
sesiones DRM/Pixman a 1280×720 verificaron Enter/Espacio desde uinput, 0→1→2,
cierre con Escape y reapertura persistente 2→3. Las capturas DRM y del cliente
coinciden exactamente en RGB. Los procesos y sesiones se cerraron y volvió tty1.
Ver APK-WAYLAND.md y reports/a2-wayland/. A2 está verificado para la fixture,
sin acreditar otras APK, mando físico, seguridad o estabilidad prolongada.

La siguiente dirección solicitada es portar componentes originales del framework
AOSP, adaptando dependencias a Linux. Las clases android.* actuales son propias;
la prueba existente será regresión durante ese port, no su resultado final.

## Compilación y primer enlace del framework original

Las fuentes originales fijadas de Looper, Handler, Message y MessageQueue compilan
sin cambios y se convierten a DEX. La referencia completa de API internas y las
dos declaraciones auxiliares son sólo de compilación y no están en ese DEX.
ART ejecuta Looper.prepare hasta el constructor original de MessageQueue, que
falla en nativeInit por ausencia de JNI. FileDescriptor.getInt$ se verificó en
el ART real. Aún no hay cola funcional ni sustitución de las API del contador.
Ver runtime/aosp/README.md y reports/aosp-queue-compile/.

## Puente JNI Rust de MessageQueue probado

Los seis métodos JNI se enlazan con epoll/eventfd. Pasan cuatro pruebas Rust con
FD reales y una prueba ART de creación, espera, despertar entre hilos, listener
Java público sobre una tubería y destrucción. SparseArray y tres utilidades se
compilan desde fuentes AOSP sin cambios, junto con las cuatro clases de la cola.
HandlerDispatchProbe aún falla por Parcelable ausente: no se acredita despacho
Java ni integración del framework original con la APK. Ver AOSP-JNI-LINUX.md y
reports/aosp-queue-jni/.

## Despacho Handler/Looper original verificado en Linux local

Se compilan 19 fuentes originales sin cambios. El adaptador Rust añade relojes
Linux, identidad local y lectura de propiedades del anfitrión. Handler.post y
Looper.loop pasan un Runnable y pruebas de orden, cancelación, diferidos, idle,
hilos cruzados, WorkSource, barreras, quit y quitSafely; la cola se repitió en diez
procesos ART. Binder IPC y el servicio global de propiedades no están implementados.
Un primer timeout quedó sin diagnóstico; se conserva ese límite en el informe y
no se considera resuelta la estabilidad. La APK aún usa el runtime anterior.
Ver AOSP-HANDLER-LINUX.md y reports/aosp-handler-foundations/.

## El principal original está integrado en la APK

El contador original ya crea y modifica sus vistas mediante mensajes de Handler
en el Looper principal AOSP, con comprobación de getMainLooper y del hilo main.
Pasan persistencia, 64 activaciones sin pérdidas, EOF, fallo de comando y reapertura.
La regresión DRM/Pixman 720p con uinput pasa y los frames coinciden exactamente
con las capturas DRM. Waydroid siguió inactivo y se liberaron sesión/procesos.
Ver APK-LOOPER-AOSP.md y los informes aosp-ui-headless y aosp-main-ui-wayland.
Activity/View/Bundle/recursos y preferencias siguen siendo propios; aún falta el
redibujado por cambios asíncronos y el resto del port, seguridad y estabilidad.
