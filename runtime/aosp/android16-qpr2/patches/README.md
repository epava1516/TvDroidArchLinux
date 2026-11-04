# Adaptaciones locales AOSP16 QPR2

Estas modificaciones no son código upstream ni un runtime instalado. La revisión
base permanece fijada en el manifiesto; conservar licencias y procedencia AOSP.

- `libcutils-memfd-original-label.patch`: candidato experimental de la biblioteca
  Bionic completa, sobre system/core e9d1fa3705d7fbd0ac1c942bc4c276161bfbfed1.
  Recupera las funciones de asignación/etiquetado del [cambio AOSP
  bc5465980cc6](https://android.googlesource.com/platform/system/core/+/bc5465980cc6ecc26eb7fa9e5d08a2f5921d05ed),
  [revertido por AOSP](https://android.googlesource.com/platform/system/core/+/0e78ca50b705413afff4472abaec20755075b921)
  por b/448179325, cuyo detalle técnico no es público en ese commit. Conserva su
  fallo real de asignación si no puede aplicar el contexto leído del fichero de
  política original; no fija un SID en el código ni amplía permisos de tmpfs.
  El JSON adjunto fija hashes, alcance y comparación con un port Linux existente.
  Ese port permite continuar sin reetiquetar y excluye UID aislados por una
  incompatibilidad seccomp de Chromium que comunica; esas variantes no se han
  adoptado ni validado aquí. Procesos aislados, recuperación y compatibilidad
  general quedan sin aceptar. Los filtros originales de mediaextractor y
  mediacodec incluyen fsetxattr; esto no sustituye la ejecución. El constructor
  `reports/android16-package-bootstrap/build-libcutils-memory.py` conserva el
  conjunto completo de fuentes/exports de plataforma. La prueba integrada usa
  un bind readonly privado de la biblioteca; no modifica el GSI de referencia.

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

- `0003-linux-property-action-coordinator.patch`: después de0001/0002; reutiliza
  eventfd/ActionManager originales en entrada Linux explícita. No carga RC generales
  ni SecondStageMain. API serializada con Epoll propietario; reporta acciones
  pendientes antes de completar cierre. En modo opt-in, ctl/power sin backend se
  rechazan tras checks originales; no éxito ficticio ni backend implementado.
  [Pruebas](../../../../reports/android16-property-actions/findings.json): acción
  programática/expansión y drenaje pendientes observados con comandos de regresión,
  ownership y recursos. No supervisor completo, mapa builtin/RC, MAC ni APK aceptados.

- `0004-linux-admitted-lazy-services.patch`: conserva el control original para
  las interfaces admitidas explícitamente por el coordinador Linux. No admite
  servicios o controles de energía arbitrarios.

- `0005-linux-restorecon-owner.patch`: después de0001–0004. Adapta únicamente la
  identificación de la respuesta del trabajador restorecon: compara el PID del
  peer obtenido por el kernel con `getpid()` del coordinador, en lugar de PID1.
  `CheckPermissions` sigue ejecutándose antes de esa comparación. El original
  usa PID1 porque pertenece a init; nuestro proceso supervisado Linux tiene otro
  PID. Mantener la constante vuelve a encolar su propia respuesta y no publica
  la finalización esperada por vold. La aplicación y compilación están comprobadas;
  132 demuestra restorecon CE completado y RUNNING_UNLOCKED; no acepta la
  compatibilidad completa de Markor ni autorización MAC. Véase
  [el resultado](../../../../reports/android16-package-bootstrap/original-user-unlock-progress.json).

Para reconstruir esta cadena sin sobrescribir los experimentos anteriores:

```sh
python reports/android16-property-actions/apply-patch-chain.py dist/aosp16/property-actions-source-4
python reports/android16-property-actions/build-lazy-control.py dist/aosp16/property-actions-build-5 dist/aosp16/property-actions-source-4
```

Ambos destinos deben ser nuevos. El constructor integrado comprueba los hashes
de la cadena aplicada y del archivo nativo; esto no sustituye su ejecución.
