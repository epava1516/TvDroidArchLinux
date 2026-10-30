# Primer runtime APK: ART y API mínima

Este directorio contiene el primer subconjunto de API anfitriona. ART ejecuta
el DEX original de la aplicación; las clases android.* de este directorio resuelven
las llamadas necesarias para la fixture del contador. El bucle UI usa
Looper/Handler/MessageQueue originales de AOSP. Los recursos usan también
Resources/AssetManager/ApkAssets/StringBlock originales y libandroidfw mediante JNI. No se recompilan las fuentes de la APK
ni se incorpora su MainActivity al DEX del runtime.

El árbol de View se emite como JSON para archtv-apk-host, cliente Wayland en Rust
probado en DRM/Pixman a 720p. El runtime no dibuja una pantalla prefabricada ni calcula
el contador: esos cambios los produce onClick de la APK.

## Construcción y prueba

Requiere las herramientas fijadas del laboratorio APK, JDK 17 y el conjunto ART host
descrito en docs/ESTUDIO-ART-HOST.md. Requiere además la biblioteca Rust y un build
AOSP con framework.jar generado con --with-public-resources, siguiendo runtime/aosp/README.md.
La biblioteca de recursos y sus instrucciones están en docs/AOSP-RECURSOS-LINUX.md. Los destinos deben ser nuevos.

```bash
CARGO_TARGET_DIR="$HOME/.cache/archtv/smithay/target" cargo build --offline -j1 -p archtv-aosp-linux
python tools/apk/build_aosp_queue.py --sources "$HOME/.cache/archtv/aosp-framework-study/pinned" --reference "$HOME/.cache/archtv/aosp-compile-tools/android-all-13.jar" --tools "$HOME/.cache/archtv/apk-build-tools" --output dist/apk/framework-nuevo
python tools/apk/build_apk_runtime.py --tools "$HOME/.cache/archtv/apk-build-tools" --aosp-build dist/apk/framework-nuevo --output dist/apk/runtime-nuevo
python tools/apk/verify_counter_headless.py --art "$HOME/.cache/archtv/art-host/host/art-13.0.0" --runtime-dex dist/apk/runtime-nuevo/dex/classes.dex --linux-library "$HOME/.cache/archtv/smithay/target/debug/libarchtv_aosp_linux.so" --output dist/apk/contador-prueba-nueva
```

El comprobador fija el hash de la APK original y comprueba que el runtime no define
clases org.archtv.probe. Ejecuta dos procesos para verificar 0→1→2 y reapertura
2→3; valida texto, foco, estructura y permisos del estado. Un propietario vivo
bloquea el acceso de otro proceso y libera el bloqueo al cerrar. Una variante
separada sin firma conserva el DEX y cambia un texto de resources.arsc: comprueba
que la salida proviene de recursos reales. También rechaza recursos truncados y
preferencias corruptas sin sustituirlas por cero.

## Límites actuales

- Sólo se ha probado nuestra APK Java propia, sin JNI ni dependencias adicionales.
- Activity implementa la secuencia básica de creación/cierre; no reproduce toda la
  jerarquía Android, tareas, intents, recreación ni restauración de Bundle.
- Recursos: las cadenas y referencias se resuelven en el framework original
  mediante un adaptador de inicialización sin recursos de sistema ni overlays.
  Se conserva el presupuesto de tabla de 16 MiB; ya no se usa el parser propio.
  Sólo están probadas las cadenas de la fixture y su variante; estilos, layouts,
  drawables, selección de locale y otros formatos siguen pendientes.
- View conserva árbol, texto, padding, orientación, listener y foco solicitado.
  El cliente Rust ofrece disposición básica y activación por teclado en Wayland;
  no reproduce layout/renderizado Android completo. Ver docs/APK-WAYLAND.md.
- SharedPreferences sólo ofrece getInt/edit/putInt/commit con MODE_PRIVATE.
  El formato de disco es propio; no intercambia XML de Android. commit sincroniza
  el archivo temporal y hace rename atómico, pero no se ha demostrado resistencia
  a cortes de alimentación ni se sincroniza el directorio padre.
- Se ejecuta un único APK por proceso con un directorio de datos exclusivo. Esto
  no constituye aislamiento de seguridad. Faltan firma/permisos de instalación,
  classloader por aplicación, límites globales de recursos y servicios de sistema.

Las APIs ausentes producen errores de enlace o excepciones. Las pruebas de esta
fixture no demuestran compatibilidad general ni estabilidad prolongada.
El contrato experimental está en docs/CONTRATO-APK.md.

La integración original del principal y las pruebas de ráfaga, EOF, error y
Wayland están descritas en docs/APK-LOOPER-AOSP.md. El lector tiene 16 comandos
pendientes como máximo; los callbacks de la APK se despachan en main mediante Handler.

El runtime exige -Darchtv.resources.library; el cliente Rust usa
ARCHTV_APK_RESOURCES_LIBRARY y la prueba headless --resources-library.
El gestor original y sus ApkAssets se cierran en finally tras finalizar UI,
incluso en errores de callback. La regresión actual figura en
reports/aosp-resources-headless/ y reports/aosp-resources-wayland/.

Main activa el perfil experimental x86_64/API 33 antes de construir Resources.
Sus seis propiedades son inmutables y prevalecen sobre el entorno; esto no
acredita compatibilidad completa API 33 ni NDK/Bionic. La lectura de texto usa
Resources.getString directamente. Ver docs/AOSP-RESOURCES-PUBLICO.md y
reports/aosp-public-resources-headless/ / reports/aosp-public-resources-wayland/.
Las métricas del adaptador siguen fijadas a 1280×720 durante esta fase.
