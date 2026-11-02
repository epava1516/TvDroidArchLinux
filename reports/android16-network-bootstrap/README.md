# Red original AOSP en la cohorte Linux

[Resultado verificable](functional.json): NetBpfLoad Mainline y bpfloader platform
originales terminan con código0 en la misma cohorte APEX41. El recorrido completo
sale1: netd conserva su barrera original de configuración de namespaces APEX.
No prueba conectividad, autorización MAC ni una etapa nueva de Markor.

Se reutiliza el ELF API36 de Tethering con su perfil no-root original `.33rc`.
Es una adaptación explícita de rol Linux; no se cambia el SDK ni se presupone
que el perfil root coexista con Linux. Según NetBpfLoad.cpp, el perfil root
exige inventario BPF global vacío y modifica unprivileged_bpf_disabled; el host
ya tiene filtros systemd/NetworkManager. No se ejecutó esa variante root.
El perfil no-root probado conserva el control global en2.

Después se ejecuta el ELF platform intacto como entrada `/archtv/bin`, tipada
bpfloader_exec para reutilizar la transición original init→bpfloader. AOSP
prohíbe que init ejecute bpfloader_platform_exec directamente. El intento directo
falló; no se añadió una excepción neverallow ni una transición inventada.
El alias bajo /vendor/bin salió1 sin diagnóstico pre-main conservado; el alias
de plataforma permite el recorrido. No atribuir sólo al cargador dinámico una
causa no capturada en aquella ejecución. `stdio_to_kmsg` no produjo diagnóstico:
el SetupStdio original requiere /dev/kmsg_debug y cae a /dev/null si falta.

boundary.py prepara bpffs nuevo en NET/MOUNT privados. Linux6.18 añade por sí
mismo maps.debug/progs.debug: se admiten sólo esos enlaces de iterador iniciales,
no pins Android ni mainline_done inventados. Conserva controles privados reales;
los JIT globales auténticos se enlazan mediante un punto intermedio ajeno a procfs.
El preparador entra temporalmente en NET anfitrión sólo para ese bind, restaura
NET privado en finally y cierra el handle antes de cualquier servicio Android.
Se comprueban dev/inode y valores reales1; no se copian archivos sysctl ficticios.
El cargador original vuelve a escribir sus valores actuales1; la comprobación
posterior acredita ausencia de cambios finales, no ausencia de toda escritura.

El observador existente conserva IDs de pins propios, identidades muestreadas y
snapshot final. El runner verifica desaparición tras cerrar namespaces/cgroups,
sin borrar BPF ajeno. Se observaron43 programas/59 mapas; ninguno queda activo.
El proceso platform fue demasiado breve para su muestreo de identidad: sigue
pendiente verificar sus capacidades efectivas. Los filtros del anfitrión no se
eliminan. No se afirma aislamiento sólo por usar namespaces: BPF conserva IDs y
efectos globales, y R1-MAC sigue abierto.

Fuentes fijadas: system/core e9d1fa3705d7fbd0ac1c942bc4c276161bfbfed1,
Connectivity f930245ec39a510f37a9a7dfaded96d287491a61,
system/bpf 0021d8d13eb1f603db6b1fa61b6d8ae4b65023db.
Contratos estudiados: NetBpfLoad.cpp, netbpfload.{33rc,35rc}, loader/bpfloader.rs,
loader/Loader.cpp, init/{builtins,mount_namespace,service}.cpp y private/bpfloader.te.
[REA MCP](platform-elf-mcp.json) verifica identidad/notas del ELF sin ejecutarlo;
la ejecución está acreditada por los logs del checkpoint, no por inspección estática.

Siguiente integración: namespaces y generación linkerconfig originales, netd y
ConnectivityModuleConnector/NetworkStackClient/NetworkManagement/NetworkStats/
NetworkPolicy/ConnectivityServiceInitializer en su orden original. No marcar
readiness manualmente ni interpretar registro de Binder como recorrido APK.
