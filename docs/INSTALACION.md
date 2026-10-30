# Base actual y herramientas conservadas

Este repositorio parte de Arch Linux ya instalado. El nuevo compositor y el shell
Rust todavía no tienen instalador. La máquina queda en consola tras retirar la
sesión gráfica anterior. No se ha modificado el particionado ni el arranque UEFI.

## Diagnóstico

```bash
./scripts/00-diagnostico.sh
./scripts/registrar-paquetes.sh
./scripts/check.sh
```

El diagnóstico es de solo lectura, tolera herramientas ausentes y no certifica
por sí mismo que cada comprobación haya pasado. El inventario guarda paquetes
reales y estado básico del sistema en reports/.

## Scripts de sistema

Ejecutar como usuario habitual. Por defecto muestran acciones; --apply las aplica.

| Script | Función |
| --- | --- |
| 10-base.sh | Instalar herramientas base y habilitar red y sincronización horaria. |
| 40-android.sh | Comprobar Binder, instalar Waydroid e inicializar VANILLA. |
| 41-android-software.sh | Aplicar el perfil software Android conservando copia de su configuración. |

No es necesario repetir estas fases para preparar el roadmap. Las instalaciones
con pacman realizan una actualización completa y conservan la confirmación
interactiva. Los scripts Android no deben confundirse con un instalador de la
futura distribución.

## Manifiestos

- base.txt: herramientas y servicios base.
- android.txt: paquete Waydroid.
- build.txt: herramientas de desarrollo Rust instaladas durante H1.
- anvil-lab.txt: paquetes usados en el laboratorio, incluido el anfitrión Weston.
- platform-candidates.txt: bibliotecas candidatas según el backend; selección pendiente.
- checks.txt: herramientas para comprobar los scripts conservados.
- apk-lab.txt: JDK, Clang y dependencias del laboratorio APK/AOSP, incluido el
  perfil gráfico host experimental (Ninja, códecs, FreeType, HarfBuzz e ICU).
  No es todavía un manifiesto de dependencias de la distribución final.

El ensayo de Anvil se prepara con los scripts 69–72. Los pasos, la revisión
y los límites de la prueba están en [el laboratorio H1](../lab/anvil/README.md).

## Android existente

Se conservan el paquete Waydroid, sus imágenes y sus datos. Las pruebas históricas
no confirmaron una interfaz usable con 1,9 GiB. Tras ampliar la VM a 7,7 GiB,
el ensayo H6 sí confirma sys.boot_completed=1 y escritorio Android nativo.
VLC se instala y lanza desde el shell; audio/vídeo y estabilidad siguen pendientes.
El perfil software configura gralloc=default y egl=swiftshader; vendor moderno
puede traducir este último a ANGLE/Pastel. No se ha reintentado Android durante
la limpieza. Su validación corresponde al hito H6 del roadmap.

Para su diagnóstico posterior: waydroid status, journalctl -u waydroid-container
y las herramientas del contenedor. No borrar imágenes o datos como paso rutinario.

## Desarrollo propio disponible

El compositor ya tiene backend DRM/Pixman comprobado en VM, además del backend
anidado. No existe todavía un paquete de sesión final. Seguir
[DESARROLLO-RUST.md](DESARROLLO-RUST.md) para compilar y ejecutar los ensayos.

`manifests/compositor-runtime.txt` registra las bibliotecas enlazadas actuales;
`reports/compositor-dynamic-libraries.txt` guarda el inventario. El backend winit
requiere además sus bibliotecas Wayland/EGL/Mesa cargadas dinámicamente. La
selección final de paquetes y su prueba en instalación limpia pertenece a H8.
