# Proveedor IHealth original para el grupo de servicios seleccionado

Objetivo funcional: ofrecer a BatteryService los datos Linux reales que necesita
el ciclo de vida de energía/idle/alarma antes de lanzar Markor. Se reutilizan
Health AIDL/default, BatteryMonitor, HealthLoop y traducción HIDL→AIDL originales.
No hay getters simulados ni proceso Android completo.

Reproducción de fuentes y build (reutiliza el toolchain y soporte ya preparados):

```
python reports/android16-health-bootstrap/acquire.py
python reports/android16-health-bootstrap/build.py dist/aosp16/health-original-build-N
```

Los pins se contrastan con manifest.lock.xml. La construcción genera familias
HIDL1.0/2.0/2.1 y AIDL4 y enlaza estrictamente contra las bibliotecas originales
Bionic/GSI. CHARGER_FORCE_NO_UI es una opción upstream; no se arranca modo charger.
El RC deriva sólo el servicio health-default del original, con UID/GID1000,
WAKE_ALARM/BLOCK_SUSPEND y transición al dominio hal_health_default. El XML VINTF
es original. La política incorpora el TE original completo, sin nuevos allow
arbitrarios ni desactivar neverallow. Su preparación no carga la política:

```
python reports/android16-health-bootstrap/prepare-policy.py dist/aosp16/health-vendor-policy-N
```

La carga global real queda registrada con backup e instrucciones de recuperación
en /home/tv/recuperacion-archtv/20261102T013427Z-health-policy. Sigue permisivo,
policyload2: no acredita autorización ni aislamiento. Se conserva la política
anterior serializada por el kernel; su hash difiere del fichero de entrada del
compilador. La restauración preparada no se ha ensayado.

[Resultado funcional](functional.json): servicio real encontrado, dumpsys original
invoca getHealthInfo, identidad/capacidades/NNP observadas; BatteryService conecta
con AIDL HAL. El sysfs de BAT0/AC se expone por bind de sólo lectura de la clase y
sus dispositivos exactos, después del etiquetado, sin relabel del anfitrión y sin
/sys/power. No se establece ro.boot.fake_battery. El filtro BPF opcional conserva
el fallback upstream si no existe; no se afirma haberlo instalado ni probado.
[REA MCP](health-elf-mcp.json) sólo identifica el ELF, no lo ejecuta.

El grupo posterior termina con error tras DeviceIdle; se preservan logs, cierre
fallido y petición vold-failed como fallos. No demuestra fase500, lanzamiento,
ventana, entrada, nota ni persistencia de Markor. La siguiente prueba incorpora
DropBox original y conserva la causa Java fuera del flujo de logs saturado.
Las notificaciones están desactivadas y el resultado799ea975 está consumido por
la ejecución activa; no necesita otra continuación en cola.
