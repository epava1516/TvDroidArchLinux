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

## Compilación en entorno limpio

Con devtools instalado y un directorio de fuentes ya generado:

```bash
ARCHTV_PACKAGE_SOURCE="$PWD/dist/packages/VERSION" ./scripts/98-package-build.sh --apply
```

El script verifica SHA256SUMS antes de usar makechrootpkg, crea una base Arch con
base-devel si falta y prepara una copia limpia para cada compilación. La receta
limita Cargo a un trabajo. El producto no se instala en el anfitrión. Requiere
sudo para devtools y acceso a los repositorios Arch, crates.io y Smithay.
ARCHTV_PACKAGE_CHROOT y ARCHTV_PACKAGE_REPORT permiten elegir caché e informes;
un bloqueo evita ejecutar simultáneamente dos instancias del script en la misma
caché. No coordina invocaciones manuales externas de makechrootpkg.

Los informes incluyen salida de compilación, commit de fuentes, receta, hashes,
metadatos y lista de archivos de los tres paquetes. Un resultado PASS de este
script acredita compilación e inspección; las pruebas de instalación y licencia
siguen siendo puertas independientes. El wrapper tiene comprobación estática;
la primera compilación limpia se inició manualmente con los mismos devtools y
su resultado se conserva en reports/h8-build/clean-build.log.

## Sesión

El wrapper detecta la primera salida DRM conectada o acepta ARCHTV_DRM_DEVICE.
ARCHTV_MODE permite seleccionar un modo anunciado por el dispositivo. Inicia
D-Bus si hace falta y retira capacidades heredadas antes de ejecutar el compositor.
Un gestor de acceso puede seleccionar la entrada Arch TV; desde una TTY activa,
archtv-session usará los permisos de logind/libseat. No configura autologin.

Las preferencias del usuario permanecen en XDG_CONFIG_HOME/archtv/settings.json;
el paquete no instala ni elimina ese archivo. El fondo original se compila como
recurso del shell, y las fuentes tipográficas se obtienen del paquete del sistema.

## Prueba del ciclo de paquetes preparada

packaging/arch/package-lifecycle.sh acepta dos directorios con los tres paquetes,
primero la versión anterior y después una versión superior. Solo permite ejecución
como root dentro de systemd-nspawn y requiere que Arch TV no esté instalado.
Se usa exclusivamente en una raíz desechable creada con base, sin compiladores.

Resuelve las dependencias de .PKGINFO, instala, actualiza, vuelve a la versión
anterior y retira los tres paquetes. Comprueba archivos con pacman, bibliotecas
con ldd, comandos --help y conservación de un archivo de preferencias. Verifica
que desaparecen los archivos de los paquetes al retirarlos. No elimina las
dependencias del sistema ni el usuario de prueba: se conserva la raíz para inspección.

El script está preparado y pasa comprobación estática; su ejecución completa
requiere dos compilaciones terminadas. Su PASS no certifica sesión gráfica,
transformación de esquemas ni aplicaciones Android. Esas pruebas siguen pendientes.

## Preferencias y recuperación entre versiones

El esquema actual de settings.json es versión 1. Los campos ausentes reciben los
valores predeterminados del esquema; no existe todavía un esquema anterior que
requiera transformación. Las actualizaciones que mantengan versión 1 conservan
favoritos, ocultos, recientes y movimiento reducido. Los archivos demasiado
grandes se conservan, y los datos corruptos se copian antes de sustituirlos.

Al volver a un binario anterior, una versión de esquema explícita distinta de 1
impide guardar sobre el archivo original. El shell puede usar valores temporales
pero conserva los bytes del archivo para que la versión compatible los recupere.
No se convierte silenciosamente un formato futuro. Una migración futura deberá
implementar y probar su transformación y recuperación antes de cambiar la versión.
Esta protección tiene una prueba Rust con dos formatos posteriores; la prueba de
actualización de paquetes en una máquina limpia sigue pendiente.

## Primera compilación e instalación comprobadas

La revisión 0.1.0.r14.g3012fbc92f7a terminó su compilación limpia y pasó nueve
pruebas (cuatro core, cinco shell). Generó los tres paquetes con SHA-256 guardados
en reports/h8-build/first-package-sha256.txt. Se instalaron mediante pacman en
una raíz Arch base separada, sin Rust, Cargo ni GCC. pacman -Qkk no encontró
archivos alterados y los tres comandos --help respondieron correctamente.

Los binarios instalados también abrieron la interfaz a 1280×720 en ese contenedor,
con el backend Wayland anidado sobre Weston headless del anfitrión y renderizado
software. Se inspeccionó la captura del shell: fondo, tipografía y navegación
visibles. El catálogo está vacío porque el sistema base no contiene aplicaciones
gráficas. Logs, captura y comando reproducible están en
reports/h8-build/first-runtime-graphics/. No acredita selección de sesión DRM,
entrada de mando ni funcionamiento Android dentro del sistema instalado.

La retirada de esta primera versión también se comprobó en el contenedor:
64 archivos de los paquetes desaparecieron, sus registros dejaron de figurar en
pacman y los bytes de un archivo de preferencias de prueba se conservaron.
Ver first-runtime-removal.log y su script reproducible en reports/h8-build/.
La raíz de prueba queda sin Arch TV instalado para el siguiente ciclo completo.

makepkg detectó referencias al directorio de compilación en ambos binarios. La
receta posterior incorpora --remap-path-prefix; su efecto aún requiere comprobar
la siguiente compilación. Esta primera versión tampoco incluye las mejoras
posteriores de avisos Cargo y protección de esquemas nuevos. La revisión
0.1.0.r22.gae035c4e2323 se está compilando desde cero con esas mejoras para probar
la actualización. H8 permanece abierto.

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
pendiente esa revisión y la revisión de los cinco avisos ausentes. La receta genera el inventario desde
el árbol Cargo de la compilación y copia ese inventario y todos los avisos
localizados a cada paquete bajo /usr/share/licenses/PAQUETE/. Esto conserva
los avisos disponibles; no transforma los cinco casos pendientes en resueltos.

## Herramientas para la imagen de distribución

El manifiesto manifests/distribution-lab.txt registra devtools y archiso como
herramientas de laboratorio, separadas de la sesión instalada. Archiso 91 está
instalado; su perfil oficial releng soporta systemd-boot UEFI. No se ha generado
una ISO propia ni validado su arranque. Versiones e instalación están guardadas
en reports/h9-preparation/. El perfil propio y el instalador siguen pendientes.

## Repositorio local de laboratorio

```bash
python packaging/arch/local-repository.py dist/packages/VERSION dist/repositories/VERSION
```

El destino debe ser nuevo. El generador exige los tres nombres de paquete, una
única versión común y un commit de fuentes válido. Copia solo esos paquetes y
genera los índices de repo-add, manifest.json con hashes y SHA256SUMS relativos.
No modifica pacman.conf ni instala paquetes. El repositorio es local, sin firma
y no constituye una publicación. La distribución deberá definir claves y política
de firma antes de ofrecer actualizaciones públicas.

La primera revisión se generó con sus tres paquetes y todos los hashes pasaron.
El consumo del índice mediante pacman en el contenedor queda registrado en
reports/h8-build/local-repository-consumption.log; la configuración de prueba
se limita a ese repositorio y una base temporal, sin cambiar el anfitrión.
