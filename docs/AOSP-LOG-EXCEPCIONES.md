# Log original con excepciones y líneas largas

El perfil original incorpora LineBreakBufferedWriter de frameworks/base Android
13 bff944d05cd47d2b3b713565d3f00d512840d282, sin modificar su fuente. Sus 9.775
bytes y SHA-256 18120713e2065a24ec0a297f63edecb0af1e11d40371bf3795d0798a1e40e029
se fijan en framework-study.json. El perfil de vistas compila 106 fuentes
originales; no se incorpora android-all al classpath de ejecución.

Log.printlns ya puede utilizar el escritor original sobre el JNI Linux de Log.
No se reimplementa la separación de líneas en Java propio ni se suprime el
registro de errores para avanzar en el constructor de AccessibilityManager.

## Pruebas

verify_linux_log.py conserva los cuatro casos de filtros, precedencia de
propiedades, Unicode, tamaños y buffers del perfil anterior. Con
--with-throwables añade una fixture separada que comprueba:

- Mensaje con salto de línea, excepción exterior y causa con Unicode ñ 📺.
- El comportamiento original de UnknownHostException: conserva el mensaje y
  suprime la traza del wrapper y su causa de red.
- El mensaje especial original de DeadSystemException.
- Una línea ASCII con 12.000 caracteres de contenido y marcadores de inicio y
  fin: se cuentan los 12.000 caracteres tras dividirse en registros nativos.

La fixture llama la sobrecarga de tres argumentos con Throwable null para probar
la escritura larga; la sobrecarga simple sigue sometida al límite del registro
nativo, ya verificado por la regresión. La prueba larga ASCII no acredita
conservación de Unicode multibyte en todas las fronteras de fragmentación.

```bash
python tools/apk/verify_linux_log.py --aosp-build dist/apk/aosp-log-writer-1 --tools "$HOME/.cache/archtv/apk-build-tools" --art "$HOME/.cache/archtv/art-host/host/art-13.0.0" --linux-library "$HOME/.cache/archtv/smithay/target/debug/libarchtv_aosp_linux.so" --with-throwables --output dist/apk/log-excepciones-nuevo
```

Los comandos, hashes, resultados y salidas están en reports/aosp-log-throwables.
El informe separa throwable_log_pass de las pruebas previas. Se ejecuta en ART
con -Xint y -Xcheck:jni. No se acredita logd, anillos Android, WTF/StrictMode
completos ni todas las sobrecargas de Log.

## Avance del layout

La regresión Wayland carga el framework ampliado y el holder Binder original.
Pasan los 32 Binder, constructor/estado inicial de View, cinco medidas, consulta
de permisos, resize 960×540→800×450, animación y muerte/cierre del proveedor.

AccessibilityManager ahora registra la ausencia de recursos de foco y utiliza
el fallback implementado por AOSP. Después llega a la búsqueda del servicio
accessibility en ServiceManager, cuyo camino fuera de caché llama
BinderInternal.getContextObject. Ese JNI sigue ausente: view_layout_pass=false.
El siguiente trabajo es adaptar la búsqueda a un registro real de servicios
Linux conservando contratos e identidad; no se acredita todavía layout, dibujo
original, soporte de accesibilidad ni cierre de A3.
