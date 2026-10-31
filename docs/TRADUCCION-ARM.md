# Traducción ARM · investigación R6 separada

Estado: investigación, 2026-10-31. **No se ha implementado ni habilitado traducción.**
El runtime principal sigue siendo AOSP16 QPR2/Bionic x86_64 con Linux/Smithay.
Esta línea no cambia sus propiedades ABI, librerías, namespaces o prioridad Markor.
No hay APK ARM aprobada. API/servicios, ABI Bionic/JNI e ISA siguen siendo tres ejes.
[Evidencias y procedencia](../reports/arm-native-bridge-research/validation.json).

## Native Bridge original que reutilizar

Se estudiaron libnativebridge y libnativeloader de ART
`1690c6912a7972c9e62c39b48c706de9b8b18b4a`, la revisión del manifiesto vigente.
El [README original](https://android.googlesource.com/platform/art/+/1690c6912a7972c9e62c39b48c706de9b8b18b4a/libnativebridge/README.md)
distingue la infraestructura de integración del traductor y exige un linker invitado
para las bibliotecas traducidas, con configuración distinta de la del host.
No equivale a que ART x86_64 pueda hacer dlopen de cualquier ELF ARM.

La implementación carga `NativeBridgeItf` desde la biblioteca del proveedor en el
namespace system y pide compatibilidad con interfaz3 (namespaces). El contrato
contiene extensiones hasta v8: señales v2; namespaces v3; vendor v4; runtime/APEX
v5; pre-fork de app-zygote v6; trampolines de JNI crítico v7; identificación de
punteros traducidos v8. **No implica que todos los casos exijan versión8**: hay
rutas condicionadas por capacidad. Versiones/nombres por sí solos no prueban JNI.
[Implementación](https://android.googlesource.com/platform/art/+/1690c6912a7972c9e62c39b48c706de9b8b18b4a/libnativebridge/native_bridge.cc),
[contrato](https://android.googlesource.com/platform/art/+/1690c6912a7972c9e62c39b48c706de9b8b18b4a/libnativebridge/include/nativebridge/native_bridge.h).

Hay que conservar el flujo original de zygote/fork, inicialización por ISA y
classloader/namespace de Native Loader; JNI_OnLoad, RegisterNatives, llamadas y
callbacks Java, AttachCurrentThread, excepciones, arrays/strings/direct buffers,
TLS, señales y descarga. Los callbacks del runtime y trampolines son contratos
reales, no funciones que podamos devolver como éxitos vacíos.

REA MCP inspeccionó el ELF original libnativebridge del APEX ART:26 exports de45
entradas examinadas. Es evidencia estática del adaptador, **no de un traductor
cargado o ejecutado**. En las rutas comprobadas de nuestra GSI no están
libndk_translation.so ni libhoudini.so. El código del adaptador lleva Apache2.0;
no transfiere su licencia a un proveedor, guest libraries o bundle externo.

## Opciones existentes y estado de decisión

| Opción | Qué aporta | Android16 QPR2 / JNI / guest | Licencia y distribución | Decisión actual |
| --- | --- | --- | --- | --- |
| Native Bridge AOSP original | Integración con ART/Native Loader, no motor ARM | Contrato de nuestra revisión estudiado; proveedor y entorno invitado pendientes | Adaptador fuente Apache2.0; auditar NOTICE/dependencias del producto | Reutilizar su contrato; no sustituirlo por API propia |
| libndk_translation | Traductor empleado en imágenes del emulador; candidato para integración Native Bridge | No hay binario fijado/inspeccionado ni pruebas locales; verificar versión real de callbacks, ABI/JNI y todas las dependencias invitadas | No hay permiso de redistribución para nuestra distro acreditado; no asumirlo por poder extraer una imagen | Evaluar sólo con procedencia y términos específicos comprobados; no empaquetar |
| Houdini de Intel | Traductor distribuido históricamente como binarios con bibliotecas ARM acompañantes | Ningún artefacto actual fijado ni matriz A16-QPR2/JNI verificada. No extrapolar Android antiguo | No se verificó licencia vigente ni concesión de redistribución; la licencia de un instalador/mirror no cubre sus blobs | Candidato técnico pendiente y distribución sin resolver; no declararlo imposible ni compatible |
| QEMU linux-user | Ejecuta procesos de otra ISA, traduce syscalls/señales y ciertos ioctl | No implementa NativeBridgeItf ni hace JNI ARM dentro de ART x86_64 automáticamente. Guest linker/Bionic y cualquier proceso ART invitado son otra prueba | GPLv2, con licencias particulares por componente; revisar obligaciones del paquete elegido | Alternativa experimental/control separada, no bridge integrado ni Android completo |
| Berberis publicado por AOSP | Infraestructura de traducción y thunks existente | El README de la revisión e5ab6a1b declara riscv64→x86_64, no un backend ARM disponible por esa revisión | Revisar licencias de módulos; no confundir código publicado con binarios privados | Referencia de reutilización; no implementar ARM desde cero por esta ausencia |
| Digitalis existente | Proyecto comunitario que publica un backend ARM64 sobre Berberis y declara AOSP16 | Manifiesto apunta android16-qpr2-release y sustituye binary_translation/goldfish por forks; ramas aún no resueltas a nuestro lock. Sin build ni prueba local | Repositorio de entrada declara Apache2.0; auditar fuente del motor, terceros, guest libs y NOTICE del bundle, no heredar permiso global | Priorizar auditoría del candidato abierto existente antes de desarrollar otro motor |

Google describe traducción ARM dentro del proceso manteniendo ART y gráficos en
x86 en su [anuncio de Android11](https://android-developers.googleblog.com/2020/03/run-arm-apps-on-android-emulator.html).
Es evidencia histórica de arquitectura, no certificación A16 ni permiso para
nuestra distribución. El anuncio limita el uso a desarrollo/depuración y excluye
servicios comerciales alojados. Los [términos SDK](https://developer.android.com/studio/terms)
restringen usos y redistribución, con excepciones para componentes de código
abierto bajo sus propias licencias. Falta revisar el permiso concreto del blob.

Los [metadatos oficiales](https://dl.google.com/android/repository/sys-img/google_apis/sys-img2-3.xml)
consultados anuncian `system-images;android-36.1;google_apis;x86_64`, revisión4,
con `android-sdk-license`; no se descargó su ZIP. El mismo XML contiene otra
licencia ARM DBT para otros paquetes: no atribuirla indistintamente a todos.
La existencia del paquete no prueba su payload libndk_translation, BUILD_ID,
paridad BP4A, interfaz8, libs invitadas o compatibilidad local.

Para Houdini se localizó un [aviso Intel de2013 conservado en un mirror](https://github.com/KernelBK/android_vendor_intel_houdini):
remite a una licencia separada y no concede derechos por ese README. Es una copia
histórica, no autorización actual ni matriz de Android16. Las notas de
[Android-x86 9](https://www.android-x86.org/releases/releasenote-9-0-r2.html)
son de otro proyecto/versión. No se obtuvo ni ejecutó ningún blob Houdini.

QEMU documenta [traducción de syscalls, señales, hilos y límites de clone/atomics](https://www.qemu.org/docs/master/user/main.html)
y su [licencia](https://www.qemu.org/docs/master/about/license.html). No presumir
soporte Binder, ioctls gráficos, futex, atomics, ptrace o namespaces invitados por
la mera ejecución de un ELF. Un proceso ARM bajo QEMU precisa su entorno Bionic;
una biblioteca ARM no se transforma en biblioteca x86_64 cargable por dlopen.
No se instaló QEMU user ni se arrancó otro sistema para este estudio.

Digitalis se examinó en README/LICENSE commit
`e81431d67766f9a827b568b9137da131daecfa87`, y manifiesto/include
`c04ff674ee0926fe79e690b20493c7b2f0e380b4`:
[proyecto](https://github.com/DigitalisX64/digitalis),
[manifiesto](https://github.com/DigitalisX64/manifest).
Sus afirmaciones y demos son evidencia del proveedor; no resultados nuestros.
No se ejecutaron sus scripts ni se construyó su emulador.

## Clausura invitada y pruebas antes de elegir

El proveedor debe ser ejecutable en el host Bionic y atender una ISA invitada
concreta. Hay que inventariar guest linker, libc/libdl/libm/libc++, DT_NEEDED,
APEX/namespaces, bibliotecas NDK/proxies de gráficos/audio y dependencias JNI reales.
No mezclar versiones arbitrarias ni copiar sólo una .so. Las bibliotecas originales
que se reutilicen conservan sus licencias y requisitos de actualización propios.

Separar ARM64→x86_64, ARMv7→x86 y cualquier caso cruzado32/64. Un bridge64 no
acredita soporte ARM32; la segunda ruta puede requerir ART/Bionic/proveedor32.
Tampoco traduce servicios Google/OEM, autenticación, DRM o capacidades del hardware.

| Puerta R6 | Evidencia exigida | Estado |
| --- | --- | --- |
| R6.0 procedencia/derechos | Commit/build, ELF/ABI/hash, licencia del motor y cada bundle/guest library; derechos de uso y redistribución diferenciados | Fuentes/interfaz y metadatos estudiados; blobs cerrados sin derechos de redistribución verificados |
| R6.1 contrato y clausura | REA para artefactos obtenidos legítimamente; NativeBridgeItf/capacidades, DT_NEEDED, guest loader/namespace y fuente original disponible | Sólo adaptador original inspeccionado; proveedores no probados |
| R6.2 JNI/ISA | Flujo original zygote, JNI normal/crítico, RegisterNatives, callbacks/hilos/TLS/signales/fork y fallos honestos por32/64 | No probado; fixtures originales sólo regresiones |
| R6.3 APK real | Variante ARM original firmada de una aplicación real, por ejemplo VLC de la misma versión de nuestro control x86; hash y ABI comprobados, sin repack ni fallback x86 encubierto | Artefacto ARM representativo aún por fijar |
| R6.4 recorrido/producto | Misma matriz de nueve etapas, reproducción multimedia/JNI, persistencia, caída/cierre, aislamiento y costes medidos; instalación/actualización/rollback y licencias verificadas | No probado |

Las nueve etapas siguen siendo instalación, lanzamiento, interfaz, entrada,
función principal, persistencia, servicios, cierre y reapertura. Registrar variante,
traductor y guest bundle exactos; resultados API/ABI/ISA por separado. Un Hello
World, cargar JNI o hallar un export no acredita APK completas ni cobertura amplia.

**Un motor propio no está justificado con esta evidencia:** aún no se ha
demostrado la insuficiencia de los candidatos existentes. Antes debe documentarse
un fallo reproducible o límite concreto por opción viable, y coste/frontera de
adaptar/reutilizar frente a desarrollar. Una licencia no verificada o ausencia de
pruebas no es demostración de incompatibilidad ni razón para empezar otro traductor.
