# Estado actual y punto de entrada

Vigente: contrato **A16-QPR2-1**, recibido el 2026-10-30. Sustituye BASE-AOSP-1 en
base, estrategia nativa y prioridad gráfica. Git y artefactos prevalecen sobre
los resúmenes; no se ha completado compatibilidad amplia.

## Retomar

1. [Checkpoint](../reports/android16-configuration/checkpoint.json) y contraste con
   Git/procesos/artefactos según [CONTINUIDAD.md](CONTINUIDAD.md).
2. [Contrato íntegro vigente](CONTRATO-APK.md), [arquitectura](ARQUITECTURA.md),
   [roadmap APK](ROADMAP-A.md) y [general](../ROADMAP.md).
3. [Matriz real](COMPATIBILIDAD-APK.md) e [índice de evidencias](EVIDENCIAS.md).
4. Continuar R0→R1 sobre Android16 QPR2 nativo, sin ampliar API33 por métodos.

## Objetivo y decisiones

APK completas sin modificar, plataforma general con compatibilidad amplia para
aplicaciones arbitrarias/Android TV sobre Linux y compositor Rust/Smithay. Bionic/AOSP
es la vía principal; conservar subsistemas originales completos y sus dependencias.
Primera hipótesis gráfica: SurfaceFlinger original con salida adaptada a Wayland.
No Waydroid ni imagen/distribución Android arrancada, ni VM Android escondida.
No reiniciar **VM ni cliente** bajo este contrato. Servicios originales individuales
no equivalen automáticamente a Android completo; estudiar cierres reales.

| Clasificación | Estado verificable |
| --- | --- |
| Base elegida por contrato | Android16 QPR2/r4, x86_64 primero y diseño ARM64. Tag/rama/build y API verificados en fuentes oficiales. Elección no equivale a implementación funcionando. |
| Procedencia fijada | Manifiesto fuente/derivado y registro de las 1.013 revisiones exactas; reproducción offline y diez objetos principales verificados. GSI oficial x86_64 del mismo build/SDK36.1 verificada; linker y ayuda ART ejecutados de forma aislada. No equivalencia fuente/binario completa ni R1 aceptada. |
| Se conserva | Compositor/shell Rust, instalación/herramientas y regresiones previas útiles; H7–H9 permanecen abiertos. |
| Históricos Android13 | ART host/glibc y fixtures propias; mezcla de jars/core/JNI; loader Bionic parcial y cierre de bibliotecas. No se trasladan como validación de A16. |
| Pendiente separado | Cuatro archivos propios de JNI/bootstrap host conservados sin commit. Ensayos API33 de propiedades/configuración pausados; no área de propiedades nueva ejecutada ni cambio a producción. |
| Configuración parcial A16 | Metadatos host originales reproducibles; propiedad root validada. Servicio/área Bionic/política SELinux pendientes. |
| Herramientas | REA MCP respondió realmente; análisis ELF/APK estático previo y estado actual, sin presentarlos como ejecución ni CLI como conexión. |
| No probado | Nueve etapas de las APK sobre A16; SF→Wayland, aceleración/entrada/AV/TV, aislamiento por app/Binder, GMS/DRM/OEM/WebView, traducción ISA/32/64, presupuestos, instalación/actualización/seguridad actualizada. |

## Checkpoint y siguiente acción

Base del nuevo hito: `1c284ad`, main; contrato y manifiesto publicados. Consultar Git para HEAD/origin actuales. El snapshot local
`/home/tv/recuperacion-archtv/20261031T000306Z-a16-configuration` guarda parches,
archivos nuevos y scripts de estudio. Los logs ajenos H9 permanecen intactos.
El checkpoint registra procesos/handles y resultados; no hay ART/bwrap/build activo
observado tras las pruebas A16. No restaurar parches sin contrastar Git.

Siguiente acción: probar inicialización privilegiada aislada de áreas con Bionic
original y los metadatos generados; registrar errores reales y acceso de clientes
sin privilegios. Se han validado el serializador/lector host originales (7 tests)
y 1.384 contextos de plataforma, no el servicio ni el área Bionic.
SELinux está compilado pero inactivo: etiquetado UID1000 falla, UID0 pasa; guardar
etiquetas no prueba mediación del kernel. La clausura de `PropertyInit` y
`StartPropertyService` dentro de libinit y sus callbacks/política sigue pendiente.
[Pruebas y límites](../reports/android16-configuration/validation.json).
Después: APEX/namespaces/classpaths originales, DEX y Markor de nueve etapas.
La ayuda ART pasa con StatsD original; rutas aplanadas aún diagnósticas. No Android
arrancado, no reinicio ni ampliación de API33 por métodos. R1 completo permanece abierto.

## Historial conservado · no es el estado vigente


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
