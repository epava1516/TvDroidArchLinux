# Alternativas de entrada · sólo offline

Estos módulos no están en el perfil canónico ni instalados/cargados en el kernel.
Se aplican al candidato Linux/AOSP compuesto, no a una política Android aislada.
Conservar todas las aserciones y los inputs fijados por el constructor existente.
[Resultados](../../../../../reports/android16-policy-launcher-entry/findings.json).

- `launcher-automatic.cil`: control que conserva usuario y rol Linux durante exec.
  Añadir un tipo destino no conserva por sí solo la identidad Android original
  ni garantiza que su siguiente transición de servicio tenga contexto válido.
- `launcher-explicit.cil`: candidato con el contexto de origen experimental
  `linux.system_u:archtv_launcher_r:archtv_launcher:s0`, rol exclusivo, y exec
  explícito hacia `u:r:init:s0`. No hay transición automática que lo seleccione.
  Extiende `linux.process_uncond_exempt` sólo con el nuevo actor para permitir
  cambiar usuario/rol en esa frontera; no desactiva globalmente las restricciones.
  Añade roleallow exclusivamente desde su rol nuevo. Las AV y neverallow acotan
  la transición a init, prohíben dyntransition y mantienen denegada administración
  de selinuxfs al coordinador y escritura a apps en los casos declarados.

El actor hereda permisos genéricos al pertenecer a linux.domain: las consultas
seleccionadas no prueban mínimo privilegio total ni equivalencia de la política.
La administración/etiquetado del ejecutable corresponde a instalación controlada,
no a permitir que el propio lanzador lo reescriba o reetiquete.

El tipo init original conserva privilegios Android amplios. Se reutiliza como
identidad del coordinador Bionic con entrada Linux propia; no implica ejecutar
SecondStageMain, boot scripts ni iniciar Android completo. Montajes, capacidades,
FD, datos, dispositivos y cgroups requieren integración y pruebas independientes.

Pendiente: demostrar cómo un sujeto Linux real entra al nuevo rol/tipo, con el
systemd anfitrión -SELINUX, labels efectivos y control de quién puede solicitarlo.
Declarar un contexto válido offline no lo asigna a ningún proceso del anfitrión.
La política sigue siendo global: aplicar S0–S2 y solicitar autorización específica
antes de carga, y otra para enforcing según el plan canónico de arquitectura.

La [auditoría de herencia](../../../../../reports/android16-launcher-permission-audit/findings.json)
distingue potenciales reglas de salida/entrada de decisiones originales concretas.
No se ha justificado aún necesidad de lockdown/textrel execmod heredados ni
validado el conjunto en ejecución; no quitar atributos sólo para aparentar
mínimo privilegio. El actor no puede realizar administración privilegiada
examinada: resolver preparación en padre de confianza y entrada específica por
ejecutable/rol, con original kernel, antes de cualquier aprobación de despliegue.

`launcher-bootstrap.cil` añade entrada offline desde linux.init_t por archivo y
rol exclusivo, permisos NNP/nosuid sólo en el prefijo y SIGKILL del padre hacia
init. Prohíbe globalmente crear/modificar/reetiquetar el tipo del ejecutable.
[Resultados](../../../../../reports/android16-launcher-bootstrap/findings.json):
fuente INIT/kernel alias, 51 consultas, cuatro compilaciones. No está instalado;
productor, identidad/inode y confianza de instalación sin demostrar. Seis permisos
NNP/nosuid de gestores siguen denegados. No eliminar NNP ni cargar política como
consecuencia de este modelo. Perfil canónico intacto.
