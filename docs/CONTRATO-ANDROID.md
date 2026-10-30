# Contrato Android A0 · borrador v1

El contrato separa el shell y el compositor del proveedor que administra Android.
La definición Rust está en crates/archtv-core/src/android.rs y no introduce
bibliotecas Android en el núcleo. Es una interfaz interna compilable: todavía
no hay servicio, transporte IPC ni adaptador que implemente AndroidProvider.
Las llamadas Waydroid actuales del shell aún no se han migrado.

## Identidad y negociación

ProviderInfo identifica proveedor y versión, versión de contrato, nivel de API
conocido, ABIs ejecutables y capacidades. El identificador del proveedor es
informativo; el shell no decide comandos según ese nombre. Una capacidad no
anunciada produce Unsupported. Una versión mayor no reconocida impide conectar;
la política de compatibilidad deberá probarse antes de congelar v1.

AppId contiene paquete Android y perfil numérico. La identidad global incluye
además el proveedor seleccionado. No se usa una etiqueta traducida, un archivo
.desktop, PID ni Wayland app_id como identidad autenticada. v1 admite un subconjunto
ASCII explícito: 1–255 bytes, segmentos separados por puntos, letra inicial y
resto alfanumérico o guion bajo. El paquete de sistema android también es válido.
El perfil Android identifica datos; no concede permiso para acceder a ellos.

El proveedor declara ABIs realmente disponibles. Compartir kernel no traduce
bibliotecas ARM a x86_64. Versión de APK o nivel de API desconocidos se expresan
como None; no se inventa un cero ni una compatibilidad no comprobada.

## Operaciones y resultados

| Operación | Resultado y condición |
| --- | --- |
| info | Metadatos y capacidades del adaptador, sin iniciar Android. |
| status | Estado de sesión y confirmación de boot por separado. |
| start_runtime | Solicitud aceptada; el shell consulta status hasta confirmar boot. |
| stop_runtime | Detención confirmada; no desinstala apps ni borra datos. |
| list_apps | Inventario del perfil con identidad, etiqueta, versión conocida y estado. |
| app_status | Running/Stopped/Unknown; no implica foco ni ventana visible. |
| install_apk | APK previamente abierto, perfil y política NewOnly/Replace; recibo del paquete resultante. |
| launch | Recibo de operación aceptada; no equivale a primer frame presentado. |
| force_stop | Detiene ejecución del paquete; conserva instalación y datos. |

Ready exige sesión Running y BootState::Completed. Ni el proceso del contenedor,
ni una propiedad vacía, ni una confirmación antigua en una sesión parada bastan.
El adaptador inicial deberá obtener una confirmación nueva y exacta de
sys.boot_completed=1. Esto tampoco certifica audio/vídeo, respuesta de la app o
compatibilidad: cada una mantiene sus propias pruebas.

NewOnly rechaza una instalación existente. Replace mantiene datos y exige que la
plataforma acepte firma y versión. Downgrade, borrado de datos y desinstalación
no se esconden en estas operaciones; necesitarán contratos explícitos posteriores.
Un recibo de lanzamiento no autentica una superficie: la asociación de ventanas
requiere un canal de confianza del proveedor al compositor. No se confía en un
app_id enviado libremente por un cliente Wayland.

## Plazos y errores

Las operaciones bloqueantes se ejecutan en workers. Reciben un plazo absoluto
Instant y deben acotar lectura, proceso hijo, espera y limpieza. El trait expresa
esa obligación; todavía no hay ejecutor que la haga cumplir. La cancelación y
el cierre del shell deberán probarse contra cada adaptador real.

Errores estables: Unavailable, NotReady, TimedOut, PermissionDenied,
InvalidRequest, IncompatibleAbi, Unsupported, NotFound, Conflict y BackendFailure.
La UI traduce códigos. La salida cruda de comandos no se muestra como error del
contrato. effect_applied distingue efecto confirmado, ausencia de efecto y estado
desconocido. Una mutación que agota su plazo puede haber ocurrido: no se repite
automáticamente cuando effect_applied es None; primero se reconcilia el estado.

La instalación recibe un descriptor prestado de un APK abierto para lectura.
El adaptador deberá verificar acceso, límites, firma y ABI mediante la plataforma;
la extensión .apk no es validación. No se convierte una ruta en una línea de shell.
No se heredan privilegios generales de root para interpretar una petición de UI.

## Transporte y adaptación pendientes

Primero se implementará un adaptador Waydroid sobre esta interfaz, con ejecución
de comandos separada y acotada. Después se definirá un servicio Rust con socket
Unix, credenciales del par, autorización por perfil y paso de descriptores para
APK. El formato de mensajes, límites y negociación wire aún no están congelados;
CONTRACT_VERSION no es una ABI Rust ni un protocolo IPC ya implementado.

La migración del catálogo y favoritos deberá conservar identidades mediante un
mapeo explícito de entradas desktop existentes. Linux sigue usando su catálogo;
las apps Android deberán llegar por el proveedor. Inicio y foco siguen siendo
responsabilidad del compositor y no detienen el runtime como efecto colateral.

## Aceptación A0

A0 se cierra cuando Waydroid implemente el contrato, el shell lo consuma sin
comandos específicos del proveedor y pasen instalar/listar/lanzar/parar/estado,
plazos, errores y conservación de datos con APK real. Las pruebas actuales solo
cubren validación de identidad y el invariante de boot; no acreditan integración
Android ni ejecución AOSP propia. Ver ROADMAP-A.md.
