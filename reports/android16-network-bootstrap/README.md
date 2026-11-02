# Red original AOSP en la cohorte Linux

## Vigente · namespaces originales y operación netd

[Resultado y hashes](native-functional.json): inventario41 contrastado por API,
XML, versiones y montajes; generación original de linkerconfig en las fases
bootstrap y default. El cliente root ndc obtiene `110 0 lo` y `200 0 Interface
list completed` después del registro real del permission controller en AMS.
El ndc original puede devolver exit0 tras respuesta400: exigimos contenido y
códigos positivos. La consulta temprana bloqueada se conserva como negativa;
no se cambió la identidad root para evitar la comprobación original.

La cohorte sale1: display espera LmkdConnection y el principal está en registro
de StorageManagerService. Siguiente paso: lmkd original y su protocolo real.
El subgrupo Java de conectividad, las etapas APK y MAC siguen sin aceptación.
El ensayo39 contiene además un error propio Thread.start duplicado, corregido
restaurando exactamente Java del38. Su verificación APEX tiene alcance separado.

El rol Linux netd añade sólo CAP_BPF para map_create con el control global en2.
UID0/netd/NNP1/máscara0x80000074ef se observaron en el ensayo de arranque previo;
los ensayos de operación no muestrearon su identidad completa. No presentar esa
observación anterior como prueba de capacidades efectivas de la última ejecución.
Los módulos netfilter existentes se cargaron con checkpoint y revisión; ninguna
regla/ruta/sysctl del anfitrión se cambió. Las reglas netd son de NET privado.

Antes de Bionic se pivota raíz en un namespace privado y se desmonta la vista
anterior: setns original no restablece una raíz externa al chroot. El observador
queda fuera. Sólo su montaje privado de bloques comparte propagación para los
controles de dm propios. Las interfaces vienen de sysfs real montado en NET
privado, no del host. Estos hechos no prueban aislamiento de tenants.

Fuentes adicionales: system/netd 8d4a0b7420e67cec340dc37a88815d99a16abfa7,
include/binder_utils/BinderUtil.h y server/{NdcDispatcher,NetdNativeService}.cpp;
Connectivity staticlibs/netd/libnetdutils/{Utils.cpp,include/netdutils/ResponseCode.h}.

## Histórico · hito inicial de cargadores BPF


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
