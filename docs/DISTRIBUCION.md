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
