# Distribución Arch TV: perfil de laboratorio

H9 está abierto. El generador packaging/iso/prepare-profile.py prepara un perfil
Archiso desde un repositorio local verificado. No ejecuta mkarchiso, no escribe
discos ni convierte el perfil en una distribución instalada.

```bash
python packaging/iso/prepare-profile.py dist/repositories/VERSION dist/iso-profiles/NOMBRE
```

El destino debe ser nuevo. El generador comprueba SHA256SUMS, los tres nombres de
paquete y la versión de Archiso revisada (91-1). Usa únicamente la plantilla de
pacman.conf del paquete oficial y contenido explícito del generador. El registro
profile-provenance.json conserva commit, paquetes, hashes y versión de herramienta.
No recorre el directorio personal ni copia configuraciones o imágenes Android.

El perfil usa systemd-boot UEFI, linux-lts, los tres paquetes Arch TV, Waydroid,
NetworkManager, PipeWire/WirePlumber y Foot. No incluye compiladores ni Graphify.
Las dependencias transitivas se resolverán durante la construcción y deberán
registrarse. Las versiones del repositorio oficial Arch todavía no están fijadas
a un snapshot; repetir la preparación no prueba reproducibilidad de la ISO.

Es un sistema live de laboratorio con consola local root sin contraseña y sin
servidor SSH habilitado. No tiene autologin gráfico ni instalador automático.
El usuario del sistema instalado, contraseñas, idioma, elección explícita del
disco y arranque de sesión forman parte del instalador todavía pendiente. La
configuración pacman del sistema live conserva los repositorios oficiales; la
ruta del repositorio local de construcción no se incorpora a esa configuración.
El repositorio Arch TV sin firma solo se usa en este laboratorio.

Se generó dist/iso-profiles/first-lab y se comprobó la sintaxis de profiledef.sh.
Evidencia de preparación en reports/h9-preparation/. No existe todavía prueba de
construcción, arranque UEFI, instalación ni funcionamiento Android desde ISO.
Antes de publicar faltan el cierre de licencias, firma de paquetes, política de
snapshots/actualización, validación del instalador y recuperación, y las pruebas
completas H6–H9. Las imágenes Android se descargarán de forma explícita en una fase
posterior; este perfil no incorpora imágenes ni datos de la VM de desarrollo.

## Primera construcción en curso y corrección detectada

Archiso aceptó las opciones UEFI y comenzó a construir el perfil. mkinitcpio
detectó memdiskfind ausente al ejecutar el hook memdisk; pese a ello, Archiso
continuó hasta comprimir el sistema. Esta candidata no queda validada por un
código de salida global cero: contiene un aviso de initramfs potencialmente
incompleto y no se usará como prueba de arranque. El generador corregido retira
memdisk, porque el perfil UEFI no utiliza arranque BIOS por MEMDISK. La siguiente
construcción deberá confirmar que desaparece el error. SquashFS queda limitado
a un procesador para compartir la VM con la compilación de paquetes.

QEMU x86 y OVMF se instalaron como herramientas de laboratorio. Esta VM no expone
/dev/kvm; una prueba anidada usará emulación y no acreditará rendimiento H7.

## Construcción con comprobación de errores

```bash
ARCHTV_ISO_PROFILE="$PWD/dist/iso-profiles/NOMBRE" ./scripts/99-iso-build.sh --apply
```

El wrapper crea directorios nuevos para trabajo e imágenes, guarda el log y exige
una única ISO. verify-build.py rechaza errores conocidos de mkinitcpio/Archiso,
comprueba la finalización de xorriso y una entrada El Torito UEFI habilitada, y
registra SHA-256 mediante lectura en bloques. El estado CANDIDATE permite pasar a
la prueba de arranque; no acredita integridad completa del initramfs, instalación
ni ejecución Android. El escaneo cubre patrones conocidos y no detecta todos los
fallos posibles. El wrapper tiene comprobación estática y modo informativo; la
construcción corregida actual se inició manualmente antes de añadirlo.

El verificador se ejecutó contra la primera ISO: devolvió FAIL y encontró los
tres mensajes del fallo memdiskfind. El informe conserva el hash de esa imagen,
que está separada con sufijo invalid-initramfs.iso. Ver reports/h9-first-build/.

## ISO corregida construida

La segunda construcción generó correctamente el initramfs LTS y una ISO de
749 MiB. verify-build.py la clasificó CANDIDATE sin errores conocidos y con
catálogo UEFI habilitado. SHA-256:
2b0a67c8c1ca2f25fddf848da6fda89695db3b2cdaba26c7dbd8bd538aa6c952.
Ver reports/h9-fixed-build/.

La prueba en QEMU/OVMF usa TCG, un procesador virtual, 1536 MiB, Virtio VGA y
solo la ISO de lectura. No conecta red ni discos del anfitrión. La captura
boot-progress.png muestra el kernel montando sr0 y airootfs y entrando en
systemd. Eso todavía no acredita consola operativa, instalación ni sesión gráfica.
QEMU requirió los módulos de paquete Virtio GPU/VGA, registrados en el manifiesto
del laboratorio. La VM de prueba sigue en observación para completar el arranque.

## Login y sesión nativa desde la ISO

La misma ISO llegó al login de tty1 con 6.18.59-1-lts. El asistente de primer
arranque pidió zona horaria; se omitió manualmente en esta prueba. El generador
posterior añade enlace UTC y KEYMAP=us; el perfil live-utc se generó y pasó
comprobación estática, pero todavía no se ha reconstruido su ISO.

Se inició sesión root en el sistema live y pacman confirmó los tres paquetes
r14. archtv-session abrió el compositor directamente sobre Virtio DRM y mostró
el shell y el catálogo. Desde él se abrió Foot y Home volvió al shell; las
capturas están en reports/h9-uefi-boot/. Esta prueba usa root en el laboratorio,
sin red y sin disco instalado. No sustituye la prueba con un usuario normal tras
instalar, ni acredita Android, audio, rendimiento o recuperación de fallos.
Se verificó finalmente escritura y ejecución en Foot: uname devolvió Linux.
Las entradas anteriores afectadas por modificadores y mapa de teclado quedan
visibles en la captura terminal-final.png; no se usaron como evidencia de éxito.
