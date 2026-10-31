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

- `0002-property-service-shutdown.patch`: aplicar después de0001. Añade cierre
  coordinado de receptores/escritor/restorecon con ownership del socket devuelto
  reservado al llamador. Stop serializado e idempotente; reinicio en proceso nuevo.
  [Pruebas y límites](../../../../reports/android16-property-shutdown/findings.json):
  cierre idle y petición incompleta, hilos4→1/FD4→4. Colas pendientes/restorecon
  activo y bloqueo I/O aún no probados; sin plazo de cierre garantizado. Directorio
  de sockets privado/exclusivo requerido; no es supervisor completo ni MAC aceptado.
