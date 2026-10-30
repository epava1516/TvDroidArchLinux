# APK original en el compositor propio

archtv-apk-host es el primer cliente Wayland Rust del runtime APK. Consume el árbol
real de vistas que produce el DEX de la aplicación en ART. Representa LinearLayout,
TextView y Button con una disposición básica y envía activaciones al listener de
la APK desde Enter, Espacio o Enter numérico. Escape cierra el cliente y solicita
el cierre del runtime. No calcula el contador ni contiene sus textos.

## Prueba verificada

reports/a2-wayland registra dos sesiones nativas DRM/Pixman a 1280×720. La primera
arranca la APK original en 0 y recibe Enter/Espacio por uinput→libinput→Wayland;
su código incrementa 0→1→2. Escape cierra cliente y ART. La segunda sesión abre
los mismos datos, muestra 2 y pasa a 3 tras Enter. El compositor y la sesión PAM
se cierran y se restaura tty1; no quedaron procesos archtv-apk-host, dalvikvm64
ni archtv-compositor en la comprobación posterior.

Las capturas del buffer DRM presentado coinciden exactamente, en RGB, con el último
frame del cliente de cada sesión. Ver scanout-comparison.json y las imágenes en
first/scanout.png y reopen/scanout.png. No se ha probado un mando físico, Android
completo, otras APK, rendimiento objetivo ni estabilidad prolongada.

```bash
CARGO_TARGET_DIR="$HOME/.cache/archtv/smithay/target" cargo build --offline -j1 -p archtv-apk-host
CARGO_TARGET_DIR="$HOME/.cache/archtv/smithay/target" ARCHTV_APK_RUNTIME_DEX="$PWD/dist/apk/runtime-nuevo/dex/classes.dex" ./scripts/101-apk-smoke.sh --apply
```

Requiere el runtime construido según runtime/apk/README.md, el compositor ya
compilado, ART host y una sesión local libre. El informe debe ser nuevo; puede
cambiarse con ARCHTV_APK_SMOKE_REPORT. El script usa sudo para la sesión PAM y
uinput, y restaura la VT inicial al terminar. Los datos del contador se guardan
en una caché privada fuera del repositorio.

## Límites y siguiente dirección

El lector de ART corre en otro hilo. Se limita cada línea a 1 MiB, la cola a ocho
mensajes, el árbol a 4096 nodos/32 niveles y las activaciones pendientes a 16.
El cliente espera eventos sin repintar continuamente; no se ha medido todavía su
consumo. El cierre solicita quit, espera hasta dos segundos y termina el grupo
de procesos restante. Esto no acredita recuperación ante SIGKILL del anfitrión
ni aislamiento de código no confiable.

El protocolo usa stdout del runtime y sigue siendo experimental. No implementa
layout/renderizado Android completo, temas, accesibilidad, puntero o selección de
foco con cruceta entre varias vistas. Las API android.* actuales son propias;
la nueva dirección es estudiar y portar componentes originales de AOSP y conservar
esta prueba como regresión durante su sustitución. Esta primera interfaz demuestra
la puerta funcional A2 para la fixture; no constituye el framework final portado.
