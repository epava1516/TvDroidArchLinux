# Estado actual y punto de entrada

Vigente: contrato **A16-QPR2-1**, recibido el 2026-10-30. Sustituye BASE-AOSP-1 en
base, estrategia nativa y prioridad gráfica. Git y artefactos prevalecen sobre
los resúmenes; no se ha completado compatibilidad amplia.

## Retomar

1. [Checkpoint](../reports/android16-linux-policy-namespace/checkpoint.json) y contraste con
   Git/procesos/artefactos según [CONTINUIDAD.md](CONTINUIDAD.md).
2. [Contrato íntegro vigente](CONTRATO-APK.md), [arquitectura](ARQUITECTURA.md),
   [roadmap APK](ROADMAP-A.md) y [general](../ROADMAP.md).
3. [Matriz real](COMPATIBILIDAD-APK.md) e [índice de evidencias](EVIDENCIAS.md).
4. Continuar R0→R1 sobre Android16 QPR2 nativo, sin ampliar API33 por métodos.

Investigación R6 independiente: [traducción ARM y opciones existentes](TRADUCCION-ARM.md).
No habilitada ni bloqueante del avance x86_64; el checkpoint principal anterior
sigue siendo el punto de recuperación del runtime.

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
| Procedencia fijada | Manifiesto fuente/derivado y registro de las 1.013 revisiones exactas; reproducción offline y diez objetos principales verificados. GSI oficial x86_64 del mismo build/SDK36.1 verificada; linker, ayuda ART y regresión DEX ejecutados con componentes originales y configuración generada. No equivalencia fuente/binario completa ni R1 aceptada. |
| Se conserva | Compositor/shell Rust, instalación/herramientas y regresiones previas útiles; H7–H9 permanecen abiertos. |
| Históricos Android13 | ART host/glibc y fixtures propias; mezcla de jars/core/JNI; loader Bionic parcial y cierre de bibliotecas. No se trasladan como validación de A16. |
| Pendiente separado | Cuatro archivos propios de JNI/bootstrap host conservados sin commit. Ensayos API33 de propiedades/configuración pausados, sin área ejecutada en esa línea ni cambio a producción. |
| Configuración parcial A16 | Propiedades originales170 leídas sin capacidades. ART original y RuntimeInit.main ejecutados; Binder privado permite llamar ActivityThread.main. Gestores bloqueados por SELinux inactivo; no APK aceptada. |
| Herramientas | REA MCP respondió realmente; análisis ELF/APK estático previo y estado actual, sin presentarlos como ejecución ni CLI como conexión. |
| No probado | Nueve etapas de las APK sobre A16; SF→Wayland, aceleración/entrada/AV/TV, aislamiento por app/Binder, GMS/DRM/OEM/WebView, traducción ISA/32/64, presupuestos, instalación/actualización/seguridad actualizada. |


## Diagnóstico previo de PropertyInit · superado por el perfil fuente

[Pruebas y alcance](../reports/android16-propertyinit-entry/validation.json):
146 fuentes originales de protobuf/Abseil compilan para Bionic; sus dependencias
cierran el enlace de la entrada supervisada PropertyInit (salida0). Ejecución real
del inicializador original aborta (salida127) por faltar
`/vendor/etc/selinux/plat_sepolicy_vers.txt` en el perfil GSI de sólo sistema.
No readiness, sockets ni APK. El inicializador es UID0 con capacidades root en
namespaces privados; esto no acredita aislamiento de aplicaciones ni SELinux.
Siguiente: contrastar generación y selección original del perfil vendor/política,
sin fabricar valores, omitir comprobaciones o iniciar Android completo.


## Perfil de propiedades y diagnóstico previo de opciones

[Pruebas](../reports/android16-property-profile/validation.json): la regla original
sepolicy_vers y la herencia BP4A derivan el valor202504 del perfil fuente. Con esa
entrada, PropertyInit original retorna0; getprop original lee los mismos170 valores
con UID10000/capacidades0. El inicializador fue UID0, separado del lector. No se
acreditan vendor de hardware, paridad de configuración GSI, sockets ni SELinux.

App_process termina1. REA MCP/GDB observa JNI_CreateJavaVM→Runtime::Create→
ParseOptions→ParsedOptions::Usage→runtime_exit(1): falla al analizar opciones,
antes de disponibilidad de VM. La traza tiene símbolos originales ajustados a
mapeos observados; breakpoint pendiente por sí solo no habría probado esa entrada.
Debugger cerrado e inferior terminado. Próximo paso: estudiar fuentes y lista real
de opciones del arranque; no declarar ActivityThread/Markor ejecutados.


## Puerta vigente: Binder privado y política del Linux anfitrión

[Resultados](../reports/android16-binder-service-gate/validation.json): kernel LTS
6.18.59, Binder Rust integrado y montajes binderfs privados. Dos contextos asignan
dispositivos distintos y responden protocolo8 con UID10000/capacidades0; esto no
prueba transacciones o aislamiento completo. Corrigiendo el conflicto de opciones
del harness, ART original ejecuta RuntimeInit.main y llega a llamar ActivityThread.main
con Binder privado; faltan el gestor de contexto y HIDL. No Markor instalada/ejecutada.

Servicemanager original, con UID/grupos de su rc y sin capacidades, aborta en
selinux_status_open(true). SELinux está compilado pero no está entre los LSM activos.
La [documentación del kernel](https://kernel.org/doc/html/latest/admin-guide/kernel-parameters.html)
describe la selección inicial mediante CONFIG_LSM/lsm=; no confundir una biblioteca
libselinux o un archivo status con política y mediación activas.

Siguiente unidad: integrar la política, etiquetas y transiciones del runtime con
la seguridad del Linux anfitrión, preservando las comprobaciones originales de
servicios. Incluir contextos Binder/HIDL/vendor, gestores, propiedades/VINTF,
identidades por servicio/app y pruebas de registro/descubrimiento/denegación/muerte.
No cargar una política Android aislada como si sólo afectara a una carpeta ni
sustituir comprobaciones por permisos ficticios. El contrato actual impide reiniciar
la VM: preparar y validar fuentes/build/instalación y pruebas independientes;
la activación y enforcement en esta VM quedan pendientes de un arranque permitido.
No se ha cambiado el boot ni arrancado Android.


## Preparación de seguridad · herramienta y compilación offline

[Validación](../reports/android16-host-security-preflight/validation.json): diagnóstico
de sólo lectura, ocho regresiones y comprobaciones con/sin permisos elevados;
la VM no satisface los requisitos de SELinux. Las capturas offline no acreditan
un kernel vivo. Host libsepol/secilc originales construidos; política platform CIL
de la GSI compilada con opciones originales y neverallow activo. Nada instalado,
cargado o reetiquetado, ni host/servicios/APK aceptados. Siguiente: comparar las
bases de política AOSP+Linux y refpolicy+contratos AOSP antes de elegir/desplegar.


## Comparación de bases de política · pendiente de elección

[Resultados](../reports/android16-policy-base-comparison/validation.json): refpolicy
fijada por commit y verificada, baseline Linux MCS/systemd/formato30 compila offline.
Las136 clases y permisos coinciden con el CIL del compilador; AOSP platform tiene107.
Tres clases de registro/propiedades Android faltan en refpolicy. La composición
global sin adaptar falla por role object_r repetido; no prueba imposibilidad de
integración. Siguiente: herramientas semánticas existentes y fronteras de política
antes de transformar. Ningún host reetiquetado, política cargada, reinicio o APK.

## Checkpoint y siguiente acción

Base histórica del diagnóstico de entrada: `e520093`. Contrato y manifiesto publicados; consultar el checkpoint vigente y Git para HEAD/origin actuales. El snapshot local
`/home/tv/recuperacion-archtv/20261031T010916Z-a16-framework-entry` guarda parches,
archivos nuevos y scripts de estudio. Los logs ajenos H9 permanecen intactos.
El checkpoint registra procesos/handles y resultados; no hay ART/bwrap/build activo
observado tras las pruebas A16. No restaurar parches sin contrastar Git.

Siguiente unidad: enlazar/evaluar el prototipo libinit original con un entrypoint
Bionic supervisado por Linux, sin activar second_stage. El inventario de todas
las entradas presentes y su clausura directa de build está en
[la decisión](../reports/android16-boot-profile/unit-decision.json). Las 52 fuentes ya compilan y el archivo prototipo contiene 63 miembros; faltan
dependencias transitivas, callbacks/control reales, persistencia y mediación;
no añadir sólo la propiedad que permita superar el siguiente guard ni duplicar
las derivaciones originales en un mapa propio. No hay nuevo perfil ejecutable.

El build **protoc host** terminó 0 (sesión69923, 393 pasos); su resultado y los
esquemas están en [la validación](../reports/android16-original-protoc/validation.json).
Protoc25.8 original generó los tres esquemas init y sus fuentes compilaron para
Bionic; no relanzar ese build. Siguiente unidad: libinit completo con sus grupos
nativos, cabeceras exportadas y dependencias generadas reales. Los módulos
parciales no acreditan un servidor ni un recorrido APK.

[Avance de dependencias](../reports/android16-native-dependencies/validation.json):
libcap estático original construido, seis fuentes/miembros ELF y generadores
originales. No ejecutado ni prueba de permisos. Las fuentes de los otros grupos
ya adquiridas no son servicios disponibles. Protoc69923 terminó; los esquemas originales ya están generados/compilados.
Usarlos al cerrar el build de libinit, sin volver a construir el generador.

[Metadatos nativos ejecutados](../reports/android16-native-property-libraries/validation.json):
ambos módulos completos, CRT y linker originales; generación y lectura sin
capacidades y con identidad 10000 real. Nativo y host difieren en 115 bytes por
orden de prefijos empatados; árbol completo equivalente y 4.145 consultas iguales,
sin modificar artefactos ni debilitar el control de propietario. Los archivos
estáticos y el wrapper no equivalen a PropertyInit o a un servidor de propiedades.

[Flags originales](../reports/android16-original-generators/validation.json):
generador fijado por Git blob, declaraciones y cadena fuente BP4A; dos módulos
compilados, sin constantes propias. Paridad de configuración con GSI no probada;
no inferir valores de paquetes ausentes del inventario system. Símbolos privados
de init localizados en minidebug y región leída mediante REA MCP/GDB, sin arrancar
init y con debugger cerrado. Protoc69923 ya terminó; consultar el checkpoint
vigente para procesos actuales, sin asumir actividad por sus PIDs históricos.

app_process original termina 0 sin readiness: fuente y diagnóstico muestran
retorno temprano de startVm por ro.product.cpu.abilist64 ausente, antes de crear
la VM. El snapshot de 101 sólo aplica system/build.prop, mientras existen 21 valores
system_ext y 58 product, además de los derivados por init.
[Pruebas](../reports/android16-framework-entry/validation.json).
El logger es instrumentación opcional mediante API original liblog: no una API
sustituta ni un preload de producción. /probe fue denegado por el namespace;
la captura en /data conserva sus restricciones.

El requisito libdexfiled.so está declarado sin condición en el JSON original.
De 41 requisitos system es el único sin proveedor declarado en este artefacto.
La fuente explica la discrepancia, pero la biblioteca sigue ausente y el estricto
global sigue fallido. No se ha añadido un sustituto ni editado el requisito.

Markor permanece intacto y sólo estuvo en CLASSPATH: no instalado, cargado o
ejecutado de forma demostrada. La invocación directa no zygote de ActivityThread
es exploratoria, no la ruta normal de lanzamiento APK. Seguir el ciclo original
de paquetes/zygote/AMS exige Binder, identidad/política y grupos de servicios;
todavía sólo se ha estudiado en fuentes. La matriz conserva nueve etapas no
probadas. R1 y el objetivo global siguen abiertos; sin reinicios ni Android boot.

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

## Unidad nativa libinit · evidencia parcial vigente

[Validación](../reports/android16-libinit-native-unit/validation.json): las 52 fuentes
originales compilan con clang21/Bionic y perfil global original. 51 objetos se
reutilizan tras igualdad real del preprocesado y comprobación SHA; init.cpp se
compila al añadir el include exportado original de libxml2. Archivo prototipo de
63 miembros: 52 fuentes, tres protobuf, dos XSD y seis libcap. No equivale a Soong
completo: sanitización/configuración de producto y alineación de flags de los
protobuf siguen abiertas, junto al enlace y ejecución supervisada de PropertyInit.

XSDC original genera el esquema APEX; sus dos fuentes C++ compilan para Bionic.
Rust1.88 original usa su std Android x86_64, sin objetos glibc en target. La FFI
original genfslabelsversion se enlaza y ejecuta en cuatro casos reales: ausente,
válido, malformado y permiso denegado. UID10000, sin grupos/capacidades, NNP1.
El fallback original 202404 no demuestra mediación SELinux. No servidor, boot
Android, aplicación ni etapa de la matriz aceptados por estas pruebas.


## Decisiones offline con herramientas originales

[Evidencias](../reports/android16-policy-semantic-baselines/validation.json): diez
consultas de inventario y catorce consultas de acceso mediante libsepol original:
seis permisos concedidos, tres denegaciones y cinco errores de contexto/clase/permiso.
Los errores no se contabilizan como denegaciones. Un permiso por invocación evita
el límite identificado en el bucle original de argumentos. No hay enforcement
vivo, política compuesta ni aceptación de aplicaciones.

Se descarta usar sepolicy-check como oráculo general: no representa todas las
condiciones efectivas y su máscara de permisos es limitada. seamendc tampoco es
un compositor completo: omite construcciones y nunca debe sustituir las aserciones
neverallow originales. La siguiente unidad debe conservar las fuentes completas,
resolver clases, atributos, usuarios/roles y MLS explícitamente y contrastar
semántica global; catorce casos no demuestran equivalencia. Ninguna base elegida.

## Control experimental de namespaces de política

[Resultados](../reports/android16-policy-namespace-controls/validation.json): el
compilador original rechaza sensibilidad/categorías dentro de bloques. Mover sólo
esas declaraciones al nivel global permite compilar AOSP (salida0 en29,8s tras
un primer límite de25s). Nueve consultas seleccionadas conservan su resultado
con nombres prefijados; no acreditan equivalencia completa. La clase original
service_manager deja de existir y aosp.service_manager no conserva su contrato
de nombre. Usuarios/roles/tipos/contextos también cambian. No es una política
de despliegue ni composición Linux/AOSP aprobada. Siguiente: preservar contratos
Android de clases/contextos y resolver explícitamente los globales MLS/SID y
la integración Linux, conservando todas las aserciones. Nada cargado o reiniciado.

## Integración de política · namespace Linux y conflicto de SID

[Ensayos](../reports/android16-linux-policy-namespace/validation.json): refpolicy
completa compila en namespace Linux con clases/common/MLS y nombres SID globales.
Cinco consultas seleccionadas con clases originales mantienen sus resultados;
no prueban equivalencia completa ni etiquetas/transiciones del host. Una unión
explícita propuesta contiene145 clases y como máximo32 permisos por clase.

El control de composición conserva reglas/aserciones de ambas fuentes, mantiene
nombres Android y separa símbolos Linux; el compilador original lo rechaza
porque un SID inicial no puede tener dos contextos. Hay27 contextos iniciales
literalmente distintos entre las fuentes. La siguiente decisión debe justificar
qué contexto global representa cada SID y cómo conservar la mediación Android
y Linux, junto a restricciones MLS y accesos entre dominios. No eliminar
contextos/asserts para aceptar una compilación. Ninguna política elegida, cargada
o validada con servicios/APK; no se reinició la VM.
