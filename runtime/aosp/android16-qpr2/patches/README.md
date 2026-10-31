# Adaptaciones locales AOSP16 QPR2

Estas modificaciones no son código upstream ni un runtime instalado. La revisión
base permanece fijada en el manifiesto; conservar licencias y procedencia AOSP.

- `0001-property-persistence-errors.patch`: system/core
  e9d1fa3705d7fbd0ac1c942bc4c276161bfbfed1, tres archivos bajo init/.
  Añade API comprobable conservando wrapper void y propaga errores en llamadores
  síncrono/asíncrono; comprueba fsync de archivo/directorio. No garantiza rollback
  de memoria ni del rename ya visible. Aplicar a copia limpia de system/core con
  `patch --batch --fuzz=0 -p1`; no editar la caché de fuentes originales.
  [Evidencias](../../../../reports/android16-property-errors/findings.json):
  compilación/enlace y ejecución de funciones comprobadas, EACCES real y EIO
  inyectado. ACK por socket, MAC, ENOSPC/rename y pérdida de alimentación pendientes.
