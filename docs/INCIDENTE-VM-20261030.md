# Cuelgue completo de la VM durante H6

El usuario confirmó el 30 de octubre de 2026 que dejó de responder toda la VM,
incluida la consola Linux, y la reinició. Las horas de este informe son UTC.
Android quedó detenido tras el reinicio. No se considera un fallo resuelto.

## Evidencia guardada

reports/h6-reboot/ conserva los logs del kernel anterior y actual, sincronización
horaria, identificación de VirtualBox, interrupciones y una muestra corta de reloj.
El arranque anterior fue 745892db8a964ccea692de92d794d070 y el nuevo es
5286af21aa514be4944fb99a38102864.

- Antes de iniciar Android, a las 01:34:33, el kernel marcó TSC como inestable por
  frequency skew y cambió a kvm-clock.
- A las 02:24:06 registró un stall RCU en CPU 2/3, con 111294 jiffies, y un aviso
  de que no se produjo a tiempo el despertar del temporizador de RCU.
- La traza de CPU 2 pasa por ahci_handle_port_intr. El proceso interrumpido se
  llama systemd-timesyn; esa coincidencia no demuestra que timesyncd sea la causa.
- La búsqueda no encontró un evento OOM-kill en ese registro. El aviso RCU sobre
  un posible OOM futuro no equivale a una falta de RAM ya demostrada.

La [documentación oficial de RCU](https://docs.kernel.org/RCU/stallwarn.html)
explica que estos avisos admiten causas de planificación, interrupciones y
relojes, entre otras. Los logs acotan la investigación pero no permiten atribuir
el cuelgue únicamente a Android, Binder, almacenamiento o VirtualBox.

## Estado después del reinicio

7,7 GiB de RAM, sin swap usada y Android detenido. DMI identifica VirtualBox y
systemd-detect-virt devuelve oracle. El proveedor de paravirtualización puede
exponer características KVM sin que el hipervisor anfitrión sea QEMU/KVM.

La muestra de unos 21 s sin carga gráfica conservó TSC y no observó un salto
entre los relojes del invitado. Los relojes medidos comparten infraestructura;
no son una referencia independiente del anfitrión ni prueban estabilidad a largo
plazo. Ver clock-baseline.json para jitter y duración reales.

## Continuación

1. Conservar la identificación exacta de kernel, hipervisor, relojes y dispositivos.
2. Separar el ensayo de estabilidad de VM de la validación multimedia Android.
3. Evaluar un kernel alternativo estable y configuraciones del reloj mediante
   cambios individuales, reversibles y con informes comparables.
4. Reanudar cargas gráficas cortas antes de cualquier prueba prolongada H7.

No se ha cambiado permanentemente el reloj ni se han suprimido los avisos RCU.
La referencia oficial de [parámetros del kernel](https://kernel.org/doc/html/latest/admin-guide/kernel-parameters.html)
documenta clocksource; su existencia no prueba que forzarlo resuelva este caso.

## Alternativa LTS preparada

Se instaló linux-lts 6.18.59-1 y se generó su initramfs. La entrada separada
archtv-lts.conf conserva las opciones de raíz y microcódigo de arch.conf. Se
verificaron hashes de arch.conf y loader.conf antes/después y una segunda
invocación del helper: no cambió la selección predeterminada ni se reinició.

Binder Rust también figura como integrado en este LTS; cambiar de kernel no
constituye una comparación del driver Binder C frente a Rust. En esa fase aún faltaba arrancar LTS; el arranque y los controles posteriores
se documentan más abajo. Evidencia y hashes en
reports/h6-kernel-lts/. El script 95 reproduce la instalación y creación de la
entrada; no modifica el kernel que se está ejecutando.

La selección de un arranque concreto puede hacerse una sola vez mediante
[bootctl set-oneshot](https://www.freedesktop.org/software/systemd/man/latest/bootctl.html).
Cargar el nuevo kernel requiere reiniciar; instalarlo no acredita que corrija
el cuelgue observado.

## Arranque LTS verificado

Con autorización del usuario se realizó un reinicio con selección temporal de
archtv-lts.conf. El kernel cargado es 6.18.59-1-lts y el boot ID es
4c90fafb-d957-43fb-9628-107b4ad1e956. bootctl confirma LTS seleccionado y
arch.conf como predeterminado; loader.conf conserva default arch.conf.

El arranque registra avisos de vmwgfx sobre el hipervisor, intervalos largos del
watchdog de reloj y retraso de planificación DL. Una muestra sin carga gráfica
con 200 esperas de 100 ms duró 28,225 s: p95 de retraso 112,665 ms y máximo
330,663 ms; TSC permaneció seleccionado. No prueba una causa concreta ni permite
declarar resuelto el incidente. Android estaba STOPPED antes del ensayo gráfico.
Evidencia: reports/h6-kernel-lts/booted-lts.txt y clock-baseline.json.

La prueba nativa a 1280×720 terminó correctamente en LTS: navegación mediante
uinput, búsqueda, lanzamiento y escritura en Foot, Home/reanudación, persistencia
y reinicio del shell, volumen/silencio PipeWire y restauración de Wi-Fi. Conserva
logs y captura DRM en reports/h6-kernel-lts/native-shell/. Es una prueba funcional
corta; no acredita rendimiento H7 ni corrige los fallos multimedia H6.

## Soft lockups también con LTS

El 30 de octubre a las 08:10:43 UTC, LTS registró avisos de 28 segundos en
CPU 2 (swapper/2), CPU 0 (opt cgu.0) y CPU 3 (ALL CPUs/TCG). Coinciden con
compilación y prueba QEMU de la ISO, sin haber iniciado la prueba Android.
La CPU 2 muestra pv_native_safe_halt y la CPU 3 irqentry_exit_to_user_mode.
La presencia de compilador o TCG en una traza no demuestra causalidad.

La [documentación del watchdog del kernel](https://docs.kernel.org/admin-guide/lockup-watchdogs.html)
explica que el detector observa el tiempo transcurrido desde que su trabajo
pudo actualizar una marca temporal. Estos avisos no constituyen una prueba de
falta de RAM ni identifican por sí solos el componente responsable. No se han
desactivado detectores ni aumentado sus umbrales.

Tras terminar compilación y emulación, con Android STOPPED y 6,8 GiB disponibles,
una muestra de 200 esperas de 100 ms tardó 32,015 segundos: mediana de retraso
53,330 ms, p95 155,820 ms y máximo 223,733 ms. Conservó TSC. Las referencias de
tiempo están dentro del invitado; no son mediciones independientes del anfitrión.
Ver reports/h6-lts-stability/ para logs completos, memoria, CPU y estado del reloj.

El usuario no pudo confirmar una pausa o suspensión durante el incidente y
recordó de forma incierta un posible reinicio. El boot ID actual sigue siendo
4c90fafb-d957-43fb-9628-107b4ad1e956; no se toma ese recuerdo como prueba de
reinicio ni de su causa. La validación de estabilidad continúa abierta.

La comparación temporal con kvm-clock, anunciado por el kernel, terminó
y restauró TSC. Las mismas 200 esperas tardaron 30,622 s, con mediana de
retraso 51,112 ms, p95 112,746 ms y máximo 166,101 ms; el retraso persiste. El mecanismo sysfs está documentado por
[Red Hat](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux_for_real_time/7/html/tuning_guide/using_hardware_clocks_for_system_timestamping).
Un cambio de resultado en una muestra corta no acreditaría por sí solo una
corrección del bloqueo; el anfitrión no está instrumentado.

Tras restaurar TSC, la tercera muestra tardó 29,514 s; p95 de retraso
127,048 ms y máximo 177,357 ms. Las tres muestras conservan retrasos y
no permiten atribuir causalmente la diferencia a la fuente de reloj.
comparison-summary.json recoge el orden TSC → kvm-clock → TSC.
Android permaneció detenido durante este diagnóstico.
