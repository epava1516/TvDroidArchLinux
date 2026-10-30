# Primer runtime APK: ART y API mínima

Este directorio contiene el primer subconjunto de API anfitriona. ART ejecuta
el DEX original de la aplicación; las clases android.* de este directorio resuelven
las llamadas necesarias para la fixture del contador. No se recompilan sus fuentes
ni se incorpora su MainActivity al DEX del runtime.

La prueba actual es sin ventana. El árbol de View se emite como JSON para el futuro
cliente Wayland en Rust. El runtime no dibuja una pantalla prefabricada ni calcula
el contador: esos cambios los produce onClick de la APK.

## Construcción y prueba

Requiere las herramientas fijadas del laboratorio APK, JDK 17 y el conjunto ART host
descrito en docs/ESTUDIO-ART-HOST.md. Los destinos de salida deben ser nuevos.

```bash
python tools/apk/build_apk_runtime.py --tools "$HOME/.cache/archtv/apk-build-tools" --output dist/apk/runtime-nuevo
python tools/apk/verify_counter_headless.py --art "$HOME/.cache/archtv/art-host/host/art-13.0.0" --runtime-dex dist/apk/runtime-nuevo/dex/classes.dex --output dist/apk/contador-prueba-nueva
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
- Recursos: strings simples de configuración por defecto, UTF-8/UTF-16 y referencias
  con límite de profundidad. No estilos, XML de layouts, selección de locale,
  drawables, tablas compactas/sparse ni overlays.
- View conserva árbol, texto, padding, orientación, listener y foco solicitado.
  Layout, renderizado y entrada Wayland aún no están implementados.
- SharedPreferences sólo ofrece getInt/edit/putInt/commit con MODE_PRIVATE.
  El formato de disco es propio; no intercambia XML de Android. commit sincroniza
  el archivo temporal y hace rename atómico, pero no se ha demostrado resistencia
  a cortes de alimentación ni se sincroniza el directorio padre.
- Se ejecuta un único APK por proceso con un directorio de datos exclusivo. Esto
  no constituye aislamiento de seguridad. Faltan firma/permisos de instalación,
  classloader por aplicación, límites globales de recursos y servicios de sistema.

Las APIs ausentes producen errores de enlace o excepciones. La prueba funcional
sin ventana no demuestra compatibilidad general ni estabilidad prolongada.
El contrato experimental está en docs/CONTRATO-APK.md.
