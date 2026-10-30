# Arch TV · compositor propio para televisión

Objetivo: desarrollar un compositor Wayland ligero y específico en **Rust con
Smithay**, acompañado de una interfaz Rust inspirada en **Fire TV 2026** y soporte
de APK completas sin modificar mediante Android16 QPR2 nativo Bionic/AOSP, sin Waydroid ni arranque de un Android completo. La base prevista es Arch Linux.

El [contrato vigente](docs/CONTRATO-APK.md) prioriza subsistemas originales completos
y contrastar SurfaceFlinger con salida hacia Wayland/Smithay. La base nueva todavía
no tiene aceptación funcional; el laboratorio Android13 se conserva como historia.

El compositor propio y su cliente de prueba Rust ya están implementados para
el laboratorio anidado y salida directa DRM/KMS/Pixman desde TTY. El shell
Rust interactivo ya funciona y está en validación: navegación, favoritos, búsqueda,
aplicaciones Linux y ajustes. Android y la distribución instalable siguen pendientes. La sesión anterior y sus instaladores se han retirado.

## Documentación principal

Empieza por [Estado actual y cómo retomar](docs/ESTADO.md).
El procedimiento está en [Continuidad](docs/CONTINUIDAD.md) y los resultados
en [Evidencias](docs/EVIDENCIAS.md).

- [Mapa y seguimiento con Graphify](docs/GRAPHIFY.md)

- [Roadmap con hitos y criterios de aceptación](ROADMAP.md)
- [Diseño y medición del shell Rust](docs/DISENO-SHELL.md)
- [Compilar y probar el desarrollo Rust](docs/DESARROLLO-RUST.md)
- [Arquitectura objetivo](docs/ARQUITECTURA.md)
- [Estudio de Smithay y Anvil](docs/ESTUDIO-SMITHAY-ANVIL.md)
- [Laboratorio reproducible de Anvil](lab/anvil/README.md)
- [Referencias visuales Fire TV 2026](docs/REFERENCIAS-FIRE-TV.md)
- [Estado real y limpieza realizada](docs/ESTADO.md)
- [Base del sistema y herramientas conservadas](docs/INSTALACION.md)
- [Fuentes técnicas](docs/FUENTES.md)

## Herramientas disponibles

```bash
./scripts/00-diagnostico.sh
./scripts/check.sh
./scripts/registrar-paquetes.sh
```

Las fases `10-base.sh`, `40-android.sh` y `41-android-software.sh` siguen disponibles
como herramientas históricas de la base del sistema y el laboratorio Android. Simulan por defecto y requieren `--apply`
para aplicar cambios. No instalan un compositor ni una interfaz de TV.

Los manifiestos separan paquetes base, Android, herramientas y candidatos de la
plataforma Rust. Son listas de trabajo; no implican que estén todos instalados
ni que su selección final esté validada. El inventario real está en `reports/`.

## Laboratorio H1

```bash
./scripts/69-anvil-deps.sh --apply
./scripts/70-anvil-prepare.sh --apply
./scripts/71-anvil-build.sh --apply
./scripts/72-anvil-smoke.sh --apply
```

Usa una revisión y Cargo.lock fijados. Weston actúa como anfitrión temporal de
pruebas; el desarrollo propio y la salida directa pertenecen a los hitos siguientes.
