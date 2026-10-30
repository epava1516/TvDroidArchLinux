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
