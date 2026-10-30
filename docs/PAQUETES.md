# Paquetes Arch TV en preparación

H8 sigue abierto. La receta inicial divide el producto en tres paquetes:

| Paquete | Contenido | Dependencias principales |
| --- | --- | --- |
| archtv-compositor | Binario Rust/Smithay con DRM/Pixman y backend anidado | libinput, libseat/seatd, libudev, xkbcommon, pixman y bibliotecas Wayland/EGL/Mesa |
| archtv-shell | Launcher SCTK con arte original incluido en el binario | Wayland, xkbcommon y DejaVu Sans del sistema |
| archtv-session | Entrada de sesión Wayland y comando archtv-session | Las versiones exactas de compositor/shell, Bash, D-Bus y setpriv |

Waydroid, NetworkManager, WirePlumber y Foot son integraciones opcionales del
shell. Los compiladores, Graphify, Weston y FFmpeg pertenecen al desarrollo o
laboratorio y no se incluyen como dependencias de ejecución de la sesión.

## Fuentes y receta

```bash
./scripts/97-package-source.sh --apply
```

Requiere fuentes guardadas en Git. Archiva Cargo.toml, Cargo.lock, crates,
licencias y archivos de empaquetado del commit HEAD. Omite informes, cachés,
credenciales y material de laboratorio. Genera en dist/packages/VERSION/:

- archtv-VERSION.tar.gz, con cabecera gzip determinista.
- PKGBUILD con SHA-256 concreto y .SRCINFO generado por makepkg.
- source-commit.txt, source-date-epoch.txt y SHA256SUMS con nombres relativos.

Desde ese directorio, sha256sum --check SHA256SUMS verifica tanto el archivo
de fuentes como PKGBUILD incluso después de copiarlos a otra máquina.

El script ejecuta makepkg --verifysource. Eso verifica el archivo de fuentes,
no demuestra compilación ni instalación. La versión de paquete incluye el
número de commits y el identificador de HEAD para distinguir revisiones.
La receta usa cargo fetch --locked en prepare y --frozen para compilar/probar.
Las dependencias Cargo quedan fijadas en Cargo.lock y Smithay a su revisión Git.

## Sesión

El wrapper detecta la primera salida DRM conectada o acepta ARCHTV_DRM_DEVICE.
ARCHTV_MODE permite seleccionar un modo anunciado por el dispositivo. Inicia
D-Bus si hace falta y retira capacidades heredadas antes de ejecutar el compositor.
Un gestor de acceso puede seleccionar la entrada Arch TV; desde una TTY activa,
archtv-session usará los permisos de logind/libseat. No configura autologin.

Las preferencias del usuario permanecen en XDG_CONFIG_HOME/archtv/settings.json;
el paquete no instala ni elimina ese archivo. El fondo original se compila como
recurso del shell, y las fuentes tipográficas se obtienen del paquete del sistema.

## Puertas pendientes

1. Compilar en un entorno Arch limpio, registrar toolchain, dependencias reales,
   licencias transitivas y hashes. Contrastar deps con los binarios construidos.
2. Instalar los tres paquetes en una máquina de prueba limpia y abrir la sesión.
3. Actualizar conservando preferencias y comprobar la migración de esquemas.
4. Desinstalar y verificar archivos residuales y recuperación de la sesión.
5. Verificar la reproducibilidad binaria; un tar de fuentes idéntico por sí solo
   no prueba que el binario sea reproducible.

La estructura sigue el [formato oficial PKGBUILD](https://man.archlinux.org/man/PKGBUILD.5.en).
La auditoría de licencias de todas las dependencias precederá a publicar paquetes.

## Inventario inicial de licencias Cargo

packaging/arch/cargo-license-inventory.py contrasta el árbol normal/build de
x86_64 con los metadatos Cargo y copia los avisos disponibles. El primer inventario
identifica 177 paquetes. Los avisos que faltaban en los crates se buscan en la
revisión Git publicada por cada crate; URL y hash quedan en
licenses/cargo-supplemental/sources.json. Cinco crates siguen sin un archivo de
aviso localizado: drm-fourcc, libseat, libseat-sys, pixman y pixman-sys.

La licencia declarada y los autores publicados se conservan tal cual, sin inventar
un aviso de copyright. Encontrar un archivo de licencia no completa por sí solo
la revisión de condiciones. La preparación de paquetes de distribución mantiene
pendiente esa revisión y la inclusión completa de avisos en los paquetes binarios.
