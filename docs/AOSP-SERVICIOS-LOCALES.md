# Bootstrap de servicios originales sobre Linux

El conjunto experimental compila 82 fuentes Java originales, incorporando
WindowManagerGlobal, ServiceManager, IInterface, StatLogger y las excepciones
RemoteException/DeadObjectException/DeadSystemException/AndroidException. Las
fuentes permanecen sin modificar y con hashes fijados. La referencia completa
sigue siendo exclusivamente de compilación.

## Caché original y endpoint local

ServiceManager.initServiceCache permite instalar referencias de servicios en el
bootstrap del proceso. La prueba ART utiliza el método original y comprueba
getService, getServiceOrThrow y checkService sobre la misma referencia, así como
el rechazo original de una segunda inicialización. La ruta de caché funciona sin
invocar el contexto global de Binder.

LocalServiceBinder es un adaptador propio que implementa IBinder/IInterface
originales. Proporciona identidad de descriptor, consulta local, estado vivo y
cierre explícito del endpoint. Mantiene registros DeathRecipient, permite
eliminarlos y notifica el cierre fuera del monitor, en el hilo que llama close.
El cierre es idempotente y se notifican los demás receptores aunque uno lance
RuntimeException. Se prueban también reentrada, cierre, enlace a un endpoint
cerrado y conservación de la referencia cerrada en la caché original.

Este adaptador está en runtime/aosp/linux-services/, separado del runtime del
contador. No tiene transporte Binder IPC, dump, dumpAsync ni shellCommand: esas
operaciones lanzan UnsupportedOperationException. La notificación probada procede
del cierre local del objeto; no acredita detección de muerte de otro proceso.
Tampoco se ha implementado un servicio de ventanas o conectado el endpoint al
compositor.

La consulta de un nombre no precargado alcanza BinderInternal.getContextObject y
falla con UnsatisfiedLinkError. Se registra como GLOBAL_SERVICE_UNAVAILABLE y
trabajo pendiente, sin convertirlo en una resolución global satisfactoria.

## Contrato IWindowManager íntegro

window-aidl-sources.json fija 67 contratos AIDL, su revisión, SHA-256 y raíces de
include: frameworks/base y Surface de frameworks/native. ParcelFileDescriptor y
java.util.List son tipos integrados del compilador, comprobados mediante su
aceptación real. fetch_window_aidl_sources.py descarga únicamente esos inputs y
verifica cada archivo.

El compilador AIDL oficial, su libc++ y NOTICE están fijados en aidl-toolchain.json.
La revisión procede del tag Android 13 r3 de prebuilts/sdk; el ejecutable declara
SDK de plataforma 32. Se usa para generar directamente desde los archivos AIDL
originales, con min_sdk_version=28. El antiguo modo preprocess de ese ejecutable
emitió un cpp_header sin comillas que su propio lector rechazó; la generación
directa con el cierre de imports original funciona sin alterar los contratos.

El resultado contiene IWindowManager, Default, Stub y Stub.Proxy. Se compilan y
convierten a DEX sin copiar implementaciones de tipos importados ni bytecode de
la referencia. Coinciden las 133 firmas de método y los 133 IDs de transacción
con la referencia interna fijada. Las cuatro clases se inicializan en ART junto
al conjunto original y al probe local. No se instancia Default como servicio ni
se ejecutan operaciones de ventanas para acreditar este hito.

La comparación no acredita serialización Parcel, llamadas IPC, validación de
argumentos, permisos ni implementación de esas 133 operaciones. La carga de
clases tampoco resuelve necesariamente todos los tipos de sus métodos.

## Reproducción

```sh
python tools/apk/fetch_aidl_tools.py --cache /home/tv/.cache/archtv/aosp-aidl-tools
python tools/apk/fetch_window_aidl_sources.py \
  --cache /home/tv/.cache/archtv/aosp-framework-study/pinned --fetch
python tools/apk/generate_window_aidl.py \
  --sources /home/tv/.cache/archtv/aosp-framework-study/pinned \
  --aidl-tools /home/tv/.cache/archtv/aosp-aidl-tools \
  --tools /home/tv/.cache/archtv/apk-build-tools \
  --reference /home/tv/.cache/archtv/aosp-compile-tools/android-all-13.jar \
  --output dist/apk/window-contract-new
python tools/apk/build_aosp_queue.py --with-views \
  --sources /home/tv/.cache/archtv/aosp-framework-study/pinned \
  --reference /home/tv/.cache/archtv/aosp-compile-tools/android-all-13.jar \
  --tools /home/tv/.cache/archtv/apk-build-tools --output dist/apk/services-framework-new
python tools/apk/probe_service_cache.py \
  --aosp-build dist/apk/services-framework-new \
  --tools /home/tv/.cache/archtv/apk-build-tools \
  --art /home/tv/.cache/archtv/art-host/host/art-13.0.0 \
  --linux-library /home/tv/.cache/archtv/smithay/target/debug/libarchtv_aosp_linux.so \
  --window-bindings dist/apk/window-contract-new --output dist/apk/services-check-new
```

Los destinos deben ser nuevos. La libc++ del compilador se selecciona sólo en el
entorno de sus subprocesos de build; no cambia las bibliotecas del ART de prueba.
El probe verifica hashes de framework/bindings, origen de ServiceManager,
IInterface y StatLogger, coherencia con la referencia y los manifiestos actuales.
El DEX del adaptador no contiene clases android.*. El classpath de ART contiene
los DEX seleccionados y las cuatro clases generadas, sin el JAR de referencia.

## Frontera siguiente

El constructor original de View con recursos del sistema supera las dependencias
Java nuevas y llega a la resolución global de window: getContextObject todavía
no está enlazado. La caché local verificada ofrece una vía de bootstrap para
registrar un servicio de ventanas que delegue operaciones reales a Rust/Wayland.
Faltan ese servicio, el protocolo con el compositor, ValueAnimator/RenderNode y
la construcción/dibujo de View. El runtime de las APK mantiene su interfaz propia.

reports/aosp-service-bootstrap/ conserva compilación, generación, comparación,
prueba ART de caché/lifecycle y carga del contrato, y la frontera del constructor.
A3 sigue en curso; A4/A5 y las puertas generales de estabilidad y distribución
siguen abiertas.
