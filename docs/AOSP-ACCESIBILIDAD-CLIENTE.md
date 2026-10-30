# Cliente de accesibilidad original: contratos y frontera Binder

Se incorporan AccessibilityManager y UserHandle originales de frameworks/base
Android 13 bff944d05cd47d2b3b713565d3f00d512840d282 sin modificar. El perfil
--with-views compila ahora 105 fuentes originales. No se ha implementado todavía
un servicio de accesibilidad Linux, lector de pantalla o puente AT-SPI.

## Contratos AIDL completos

accessibility-aidl-sources.json fija 53 archivos del cierre de imports de
IAccessibilityManager e IAccessibilityManagerClient, incluidos parcelables y
contratos de entrada. Los scripts existentes aceptan --manifest y generan cada
raíz con el compilador oficial fijado. Sólo las dos interfaces seleccionadas y
sus clases internas se empaquetan; los imports sirven para resolver AIDL y los
tipos no implementados siguen siendo dependencias explícitas de ejecución.

Ambas interfaces coinciden con android-all-13 de referencia en métodos y números
de transacción. También pasa la generación predeterminada de IWindowManager con
133 métodos, preservando los campos del informe que consume su adaptador Linux.
La comparación no demuestra IPC Binder ni todos los caminos de sus proxies.
Un SHA-256 alterado de entrada AIDL se rechaza antes de generar código.

```bash
python tools/apk/fetch_window_aidl_sources.py --cache "$HOME/.cache/archtv/aosp-framework-study/pinned" --manifest runtime/aosp/accessibility-aidl-sources.json
python tools/apk/generate_window_aidl.py --sources "$HOME/.cache/archtv/aosp-framework-study/pinned" --aidl-tools "$HOME/.cache/archtv/aosp-aidl-tools" --tools "$HOME/.cache/archtv/apk-build-tools" --reference "$HOME/.cache/archtv/aosp-compile-tools/android-all-13.jar" --manifest runtime/aosp/accessibility-aidl-sources.json --output dist/apk/accessibility-aidl-nuevo
```

build_window_service_probe.py y verify_wayland_resize.py aceptan
--accessibility-bindings. Verifican hashes de JAR/DEX y la referencia de
compilación; el verificador exige el DEX con que se compiló el servicio. El
classpath ART no incluye android-all ni implementaciones extraídas de éste.

## Política de consulta de permisos

LinuxContext.checkCallingOrSelfPermission delega en la política local: no hay
almacén de concesiones ni autoridad Android de instalación, por lo que toda
consulta devuelve PERMISSION_DENIED. Un argumento null produce
IllegalArgumentException. Se verifican los dos permisos entre usuarios,
INTERNET, un permiso desconocido y null en ART. El generador comprueba ahora
132 métodos abstractos: 10 implementados y 122 explícitamente no soportados.

Esta consulta no impone aislamiento a archivos, sockets o llamadas JNI. El
proceso conserva permisos del usuario Linux; el runtime sigue siendo un
laboratorio para APK propias. En particular, UID Linux 1000 coincide con
Process.SYSTEM_UID de Android: conservar el UID real no crea una identidad de
seguridad Android válida. El modelo de identidades por APK y las comprobaciones
privilegiadas del código original requieren resolución antes de aceptar APK no
confiables. No se acredita el aislamiento de A4 con este cambio.

## Resultado y siguiente implementación

Pasan constructor/estado inicial de View, los cinco casos de medida, las consultas
de permisos y resize Wayland 960×540→800×450, política de animación y cierre/muerte
del proveedor. El layout entra en AccessibilityManager original y construye su
cliente AIDL, pero Binder original falla en getNativeBBinderHolder. Se conserva
view_layout_pass=false y el error exacto en reports/aosp-accessibility-client.

core/jni/android_util_Binder.cpp queda fijado para estudio. El código original
crea un JavaBBinderHolder y publica Binder_destroy como finalizador para
NativeAllocationRegistry. Su estado incluye referencias fuertes/débiles y un
mutex; el siguiente trabajo es portar su ciclo de vida y dependencias nativas,
con asignación y liberación reales. Después quedarán la búsqueda de servicios,
recursos de foco y los caminos de eventos. No se omiten llamadas de View ni se
registra un servicio falso para declarar layout o accesibilidad completos.
