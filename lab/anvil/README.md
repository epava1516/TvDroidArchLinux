# Laboratorio H1 · Anvil

Este laboratorio estudia el compositor de referencia de Smithay. No instala una
sesión de producto ni contiene el futuro compositor propio de Arch TV.

## Resultado registrado

H1 completado el 29 de octubre de 2026 con Rust/Cargo 1.99.1. Anvil compiló en
11 min 53 s y mostró weston-simple-shm mediante GLES/Mesa llvmpipe sobre Weston
headless/Pixman. La captura se inspeccionó y muestra el cliente con su patrón
animado. No se ha modificado el código upstream.

La muestra de 3 s del proceso Anvil de desarrollo con cliente animado dio PSS
128972 KiB y 68,64% de un núcleo de CPU. Excluye Weston y el proceso cliente;
no es un benchmark en reposo ni de la futura implementación propia.

Archivos principales:

- reports/anvil-initial-build.log: primer build completo.
- reports/anvil-build.log: revalidación con --locked.
- reports/anvil-build-environment.txt: compilador, revisión y flags.
- reports/anvil/result.txt: resultado de la prueba.
- reports/anvil/anvil.log: EGL, renderer y socket publicados.
- reports/anvil/client.log: protocolo del cliente.
- reports/anvil/metrics.txt y screen.png: medida y captura de la prueba.

Los avisos EGL/DMA-BUF del log no impidieron presentar el cliente SHM. No se ha
probado DMA-BUF de Waydroid; la salida directa y sus posibles fallos siguen en H3.

## Reproducción

Como usuario habitual, con sudo disponible para instalar dependencias:

```bash
./scripts/69-anvil-deps.sh --apply
./scripts/70-anvil-prepare.sh --apply
./scripts/71-anvil-build.sh --apply
./scripts/72-anvil-smoke.sh --apply
```

Todos estos scripts simulan por defecto. `ARCHTV_LAB_ROOT` permite cambiar la
carpeta de fuentes/compilación; el valor habitual es `~/.cache/archtv`.
El checkout se verifica contra `revision.txt`, no se alteran fuentes upstream y
se conserva aquí el Cargo.lock resuelto para el ensayo. La compilación usa un
trabajo y elimina símbolos de depuración para reducir recursos, sin convertir
el resultado en un build optimizado de producción.

La preparación necesita Git/red. La primera compilación necesita acceso a los
crates; después Cargo puede reutilizar su caché. No se instalan todos los
backends de Anvil: se selecciona winit sin funciones predeterminadas.

## Qué comprueba la prueba

1. Crea un directorio de sockets temporal con permisos 0700.
2. Arranca Weston con backend headless, renderizado Pixman y shell de quiosco.
3. Arranca Anvil como cliente Wayland del anfitrión, forzando Mesa llvmpipe.
4. Conecta weston-simple-shm al socket de Anvil, no al del anfitrión.
5. Exige commits y callbacks de frame, mide el proceso Anvil y captura la salida.
6. Termina sus procesos y elimina el directorio temporal al salir.

La captura usa el protocolo de diagnóstico de Weston, habilitado solo en ese
anfitrión temporal con sockets privados. No se abren servicios de red ni se
modifica la consola gráfica del equipo.

Los resultados quedan en reports/anvil/. Si falla una fase, revisar result.txt,
weston.log, anvil.log y client.log. El archivo de métricas corresponde a Anvil
de desarrollo con un cliente animado; no mide el compositor propio, ni el
reposo de una futura sesión de TV, ni el conjunto de Weston y el cliente.

## Límites

Una prueba anidada por software no demuestra salida DRM/KMS directa, compatibilidad
con DMA-BUF de Android, rendimiento de una interfaz completa ni control físico
del mando. Esas pruebas pertenecen a los hitos siguientes del roadmap.
