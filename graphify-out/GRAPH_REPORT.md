# Graph Report - repositorio-principal  (2026-10-30)

## Corpus Check
- 185 files · ~81,068 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 5, .xml 2, .apk 1)

## Summary
- 1637 nodes · 3058 edges · 127 communities (73 shown, 54 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 40 edges (avg confidence: 0.81)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b3ce29fc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- worker.rs
- resources-jni.cpp
- Client
- Model
- TvCompositor
- xdg_shell.rs
- subprocess
- mod.rs
- input.rs
- drm.rs
- archtv-aosp-linux/src/lib.rs
- session.rs
- Roadmap · Arch TV nativo en Rust
- 95-kernel-lts.sh
- Estudio de Smithay y Anvil
- Roadmap A · compatibilidad APK mínima sobre Linux
- Referencias Fire TV para Arch TV
- common.sh
- 72-anvil-smoke.sh
- 82-rust-smoke.sh
- Shell Rust: interfaz y mediciones
- Base actual y herramientas conservadas
- Desarrollo del compositor Rust
- Arquitectura objetivo
- 68-graphify.sh
- graphify.sh
- pathlib
- archtv-core
- 00-diagnostico.sh
- 83-drm-session.sh
- 84-drm-smoke.sh
- 85-session-smoke.sh
- AGENTS.md
- 10-base.sh
- 40-android.sh
- 41-android-software.sh
- 69-anvil-deps.sh
- 70-anvil-prepare.sh
- 71-anvil-build.sh
- 80-rust-build.sh
- 86-shell-render-probe.sh
- check.sh
- registrar-paquetes.sh
- THIRD_PARTY.md
- archtv-test-client
- ErrorKind
- 89-shell-resolutions.sh
- QueueSemanticsProbe.java
- package-lifecycle.sh
- 87-shell-session.sh
- 88-shell-smoke.sh
- 98-package-build.sh
- layout.rs
- time
- DISTRIBUCION.md
- 90-android-session.sh
- 93-android-shell-session.sh
- 91-android-client.sh
- 92-android-boot-probe.sh
- 94-android-media-probe.sh
- Cuelgue completo de la VM durante H6
- Arch TV · compositor propio para televisión
- Paquetes Arch TV en preparación
- 97-package-source.sh
- Contrato Android A0 · borrador v1
- 99-iso-build.sh
- Renderer
- Client
- archtv-android/src/lib.rs
- apk_inventory.py
- Reference
- Context
- ROADMAP.md
- SessionState
- QueueHandle
- Capa de compatibilidad APK propia sobre Linux
- Capa de compatibilidad APK propia sobre Linux
- APK mínima: contador
- android.os.Handler
- .process_input_event
- RuntimeProbe
- APK original en el compositor propio
- ART host para la capa APK
- FileDescriptor
- .onClick
- Activity
- identity.rs
- 100-apk-session.sh
- 101-apk-smoke.sh
- archtv-apk-host
- properties.rs
- Port del framework original: primer cierre de compilación
- QueueLinkProbe
- Contrato experimental del runtime APK
- Primer runtime APK: ART y API mínima
- NativeQueueProbe.java
- UnsupportedAppUsage.java
- Port selectivo del framework original a Linux
- .view
- ClientState
- clock
- .onCreate
- .metafactory
- MessageQueue original: enlace JNI Linux en Rust
- archtv-aosp-linux
- LocalContextProbe.java
- Métricas de Resources y ventana Wayland
- PublicResourcesProbe.java
- android.rs
- Handler y Looper originales ejecutan mensajes en Linux
- SharedPreferences
- AndroidProvider
- Abi
- AppId
- RuntimeStatus
- La APK usa el Looper principal original de AOSP
- Capability
- winit.rs
- Port nativo de recursos de AOSP a Linux
- ApkResources.java
- AppState
- tracing.rs

## God Nodes (most connected - your core abstractions)
1. `State` - 54 edges
2. `Client` - 48 edges
3. `Client` - 47 edges
4. `TvCompositor` - 45 edges
5. `Model` - 29 edges
6. `Action` - 20 edges
7. `start()` - 19 edges
8. `Activity` - 17 edges
9. `Queue` - 16 edges
10. `Context` - 16 edges

## Surprising Connections (you probably didn't know these)
- `Procedencia y construcción` --references--> `Reference`  [INFERRED]
  docs/AOSP-RESOURCES-PUBLICO.md → runtime/aosp/compile-stubs/java/lang/ref/Reference.java
- `MainActivity` --inherits--> `Activity`  [EXTRACTED]
  fixtures/apk/counter/src/org/archtv/probe/MainActivity.java → runtime/apk/java/android/app/Activity.java
- `MainActivity` --references--> `SharedPreferences`  [EXTRACTED]
  fixtures/apk/counter/src/org/archtv/probe/MainActivity.java → runtime/apk/java/android/content/SharedPreferences.java
- `MainActivity` --implements--> `OnClickListener`  [EXTRACTED]
  fixtures/apk/counter/src/org/archtv/probe/MainActivity.java → runtime/apk/java/android/view/View.java
- `Client` --references--> `Backend`  [INFERRED]
  crates/archtv-apk-host/src/main.rs → crates/archtv-apk-host/src/backend.rs

## Import Cycles
- None detected.

## Communities (127 total, 54 thin omitted)

### Community 0 - "worker.rs"
Cohesion: 0.06
Nodes (34): collect(), data_directories(), discover(), exec_keeps_arguments_and_shell_metacharacters_literal(), executable(), expand_exec(), locale_hidden_and_desktop_sections_are_respected(), parse_entry() (+26 more)

### Community 1 - "resources-jni.cpp"
Cohesion: 0.10
Nodes (22): fail(), guard(), Java_android_content_res_ApkAssets_nativeDestroy(), Java_android_content_res_ApkAssets_nativeGetStringBlock(), Java_android_content_res_ApkAssets_nativeLoad(), Java_android_content_res_AssetManager_nativeCreate(), Java_android_content_res_AssetManager_nativeDestroy(), Java_android_content_res_AssetManager_nativeGetResourceIdentifier() (+14 more)

### Community 3 - "Model"
Cohesion: 0.05
Nodes (47): Application, Action, AndroidStart, AndroidStop, Launch, Mute, Quit, Refresh (+39 more)

### Community 5 - "xdg_shell.rs"
Cohesion: 0.06
Nodes (3): TvCompositor, handle_commit(), TvCompositor

### Community 6 - "subprocess"
Cohesion: 0.11
Nodes (14): audio(), radio(), settings(), state(), text(), volume(), run(), verify() (+6 more)

### Community 8 - "input.rs"
Cohesion: 0.09
Nodes (5): Shortcut, Exit, Home, Resume, Vt

### Community 9 - "drm.rs"
Cohesion: 0.08
Nodes (4): Backend, init(), Result, Scanout

### Community 10 - "archtv-aosp-linux/src/lib.rs"
Cohesion: 0.12
Nodes (20): guard(), Java_android_os_MessageQueue_nativeDestroy(), Java_android_os_MessageQueue_nativeInit(), Java_android_os_MessageQueue_nativeIsPolling(), Java_android_os_MessageQueue_nativePollOnce(), Java_android_os_MessageQueue_nativeSetFileDescriptorEvents(), Java_android_os_MessageQueue_nativeWake(), lookup() (+12 more)

### Community 11 - "session.rs"
Cohesion: 0.21
Nodes (3): Result, start(), Supervisor

### Community 14 - "Roadmap · Arch TV nativo en Rust"
Cohesion: 0.13
Nodes (15): Alcance inicial, Evolución A · compatibilidad APK mínima sobre Linux, H0 · Limpieza y base documental, H1 · Rust y Anvil como laboratorio, H2 · Compositor mínimo propio, H3 · Salida directa y decisión de renderizado, H4 · Comportamiento de televisión y sesión, H5 · Interfaz Rust con referencia Fire TV 2026 (+7 more)

### Community 17 - "Estudio de Smithay y Anvil"
Cohesion: 0.40
Nodes (5): Estudio de Smithay y Anvil, Mapa de lectura, Qué no resuelve Smithay automáticamente, Revisión de referencia, Riesgo gráfico que debe resolverse primero

### Community 18 - "Roadmap A · compatibilidad APK mínima sobre Linux"
Cohesion: 0.22
Nodes (9): Corrección del enfoque anterior, DEX de la APK ejecutado con API mínima, Fixture disponible, La APK ya usa el principal original, Primer motor probado, Próximo experimento, Recursos originales: JNI aislado, Roadmap A · compatibilidad APK mínima sobre Linux (+1 more)

### Community 19 - "Referencias Fire TV para Arch TV"
Cohesion: 0.22
Nodes (9): Capturas de referencia, Catálogo de fuentes, Comparación histórica, Inicio 2026 — Amazon, Material pendiente para una reproducción precisa, Películas 2026 — Amazon, Qué debe parecerse, Referencia principal y versiones (+1 more)

### Community 20 - "common.sh"
Cohesion: 0.38
Nodes (4): manifest_packages(), packages(), run(), common.sh script

### Community 21 - "72-anvil-smoke.sh"
Cohesion: 0.29
Nodes (5): EGL_PLATFORM, GALLIUM_DRIVER, LIBGL_ALWAYS_SOFTWARE, 72-anvil-smoke.sh script, XDG_RUNTIME_DIR

### Community 22 - "82-rust-smoke.sh"
Cohesion: 0.29
Nodes (5): EGL_PLATFORM, GALLIUM_DRIVER, LIBGL_ALWAYS_SOFTWARE, 82-rust-smoke.sh script, XDG_RUNTIME_DIR

### Community 23 - "Shell Rust: interfaz y mediciones"
Cohesion: 0.18
Nodes (8): Comparación de composición con Fire TV 2026, Composición medida, Decisión provisional, Primer resultado del renderer optimizado, Reproducción, Shell Rust: interfaz y mediciones, Validación interactiva, Fuentes técnicas

### Community 24 - "Base actual y herramientas conservadas"
Cohesion: 0.33
Nodes (6): Android existente, Base actual y herramientas conservadas, Desarrollo propio disponible, Diagnóstico, Manifiestos, Scripts de sistema

### Community 25 - "Desarrollo del compositor Rust"
Cohesion: 0.29
Nodes (7): Construcción y comprobaciones, Desarrollo del compositor Rust, Ensayo del shell interactivo, Ensayo directo en VM, Límites actuales, Política y supervisión, Resoluciones del shell real

### Community 26 - "Arquitectura objetivo"
Cohesion: 0.40
Nodes (5): Arquitectura objetivo, Decisiones iniciales, Dependencias compartidas, Entrada y control, Evolución del entorno Android

### Community 27 - "68-graphify.sh"
Cohesion: 0.40
Nodes (4): GRAPHIFY_BACKEND, GRAPHIFY_MAX_WORKERS, PYTHONHASHSEED, 68-graphify.sh script

### Community 28 - "graphify.sh"
Cohesion: 0.40
Nodes (4): GRAPHIFY_BACKEND, GRAPHIFY_MAX_WORKERS, PYTHONHASHSEED, graphify.sh script

### Community 31 - "archtv-core"
Cohesion: 0.67
Nodes (4): archtv-android, archtv-compositor, archtv-core, archtv-shell

### Community 50 - "ErrorKind"
Cohesion: 0.18
Nodes (11): ErrorKind, BackendFailure, Conflict, IncompatibleAbi, InvalidRequest, NotFound, NotReady, PermissionDenied (+3 more)

### Community 51 - "89-shell-resolutions.sh"
Cohesion: 0.20
Nodes (8): EGL_PLATFORM, GALLIUM_DRIVER, LIBGL_ALWAYS_SOFTWARE, 89-shell-resolutions.sh script, XDG_CONFIG_HOME, XDG_DATA_DIRS, XDG_DATA_HOME, XDG_RUNTIME_DIR

### Community 55 - "87-shell-session.sh"
Cohesion: 0.50
Nodes (3): DBUS_SESSION_BUS_ADDRESS, LIBSEAT_BACKEND, 87-shell-session.sh script

### Community 58 - "layout.rs"
Cohesion: 0.14
Nodes (13): APP_HEIGHT, APP_STEP, APP_WIDTH, APP_Y, BANNER_HEIGHT, BANNER_Y, FEATURE_HEIGHT, FEATURE_STEP (+5 more)

### Community 59 - "time"
Cohesion: 0.14
Nodes (14): key(), text(), wait_for(), capture_matching(), key(), wait(), wait_frame_after(), event() (+6 more)

### Community 60 - "DISTRIBUCION.md"
Cohesion: 0.33
Nodes (5): Construcción con comprobación de errores, Distribución Arch TV: perfil de laboratorio, ISO corregida construida, Login y sesión nativa desde la ISO, Primera construcción en curso y corrección detectada

### Community 61 - "90-android-session.sh"
Cohesion: 0.50
Nodes (3): DBUS_SESSION_BUS_ADDRESS, LIBSEAT_BACKEND, 90-android-session.sh script

### Community 62 - "93-android-shell-session.sh"
Cohesion: 0.50
Nodes (3): DBUS_SESSION_BUS_ADDRESS, LIBSEAT_BACKEND, 93-android-shell-session.sh script

### Community 67 - "Cuelgue completo de la VM durante H6"
Cohesion: 0.25
Nodes (7): Alternativa LTS preparada, Arranque LTS verificado, Continuación, Cuelgue completo de la VM durante H6, Estado después del reinicio, Evidencia guardada, Soft lockups también con LTS

### Community 68 - "Arch TV · compositor propio para televisión"
Cohesion: 0.50
Nodes (4): Arch TV · compositor propio para televisión, Documentación principal, Herramientas disponibles, Laboratorio H1

### Community 69 - "Paquetes Arch TV en preparación"
Cohesion: 0.15
Nodes (12): Compilación en entorno limpio, Fuentes y receta, Herramientas para la imagen de distribución, Inventario inicial de licencias Cargo, Paquetes Arch TV en preparación, Preferencias y recuperación entre versiones, Primera compilación e instalación comprobadas, Prueba del ciclo de paquetes preparada (+4 more)

### Community 74 - "Contrato Android A0 · borrador v1"
Cohesion: 0.25
Nodes (7): Aceptación A0, Adaptador de estado implementado, Contrato anterior de proveedores Android · borrador sin congelar, Identidad y negociación, Operaciones y resultados, Plazos y errores, Transporte y adaptación pendientes

### Community 76 - "Renderer"
Cohesion: 0.12
Nodes (4): Message, Node, Renderer, Canvas

### Community 77 - "Client"
Cohesion: 0.09
Nodes (3): Client, main(), Starter

### Community 78 - "archtv-android/src/lib.rs"
Cohesion: 0.06
Nodes (11): command_deadline_and_output_limit_do_not_wait_for_pipe_eof(), drain(), error(), Process, run(), status_requires_exact_boot_value_and_rejects_stale_boot_for_stopped_session(), unsupported(), Waydroid (+3 more)

### Community 79 - "apk_inventory.py"
Cohesion: 0.24
Nodes (6): dex_inventory(), string(), table(), uint(), execute(), kill_group()

### Community 80 - "Reference"
Cohesion: 0.15
Nodes (6): Adaptaciones Linux, Evidencia y límites, Integración y perfil del contador, Procedencia y construcción, Resources original sobre Linux, Reference

### Community 81 - "Context"
Cohesion: 0.15
Nodes (6): Context, OnClickListener, View, ViewGroup, Button, LinearLayout

### Community 84 - "SessionState"
Cohesion: 0.33
Nodes (6): SessionState, Running, Starting, Stopped, Suspended, Unknown

### Community 85 - "QueueHandle"
Cohesion: 0.08
Nodes (3): control_fd(), run(), State

### Community 87 - "Capa de compatibilidad APK propia sobre Linux"
Cohesion: 0.40
Nodes (5): Alcance y recursos, APK propia preparada, Capa de compatibilidad APK propia sobre Linux, Primer estudio implementado, Qué se debe demostrar

### Community 88 - "Capa de compatibilidad APK propia sobre Linux"
Cohesion: 0.17
Nodes (12): Alcance y recursos, APK propia preparada, ART host ejecuta DEX en Linux, Capa de compatibilidad APK propia sobre Linux, Compilación y primer enlace del framework original, Despacho Handler/Looper original verificado en Linux local, El principal original está integrado en la APK, La APK propia ejecuta sus callbacks en Linux (+4 more)

### Community 89 - "APK mínima: contador"
Cohesion: 0.50
Nodes (3): APK mínima: contador, Construcción, Prueba que debe pasar la futura capa

### Community 90 - "android.os.Handler"
Cohesion: 0.06
Nodes (22): HandlerDispatchProbe, Runnable, QueueSemanticsProbe, Runnable, Setup, Runnable, Runnable, Setup (+14 more)

### Community 92 - "RuntimeProbe"
Cohesion: 0.39
Nodes (3): Increment, Operation, RuntimeProbe

### Community 94 - "APK original en el compositor propio"
Cohesion: 0.50
Nodes (3): APK original en el compositor propio, Límites y siguiente dirección, Prueba verificada

### Community 95 - "ART host para la capa APK"
Cohesion: 0.40
Nodes (4): ART host para la capa APK, Fuentes y alcance, Pruebas separadas, Resultado del primer experimento

### Community 97 - ".onClick"
Cohesion: 0.22
Nodes (3): Editor, IntPreferences, Transaction

### Community 99 - "identity.rs"
Cohesion: 0.23
Nodes (7): current(), Java_android_os_Binder_clearCallingIdentity(), Java_android_os_Binder_flushPendingCommands(), Java_android_os_Binder_getCallingPid(), Java_android_os_Binder_getCallingUid(), Java_android_os_Binder_isDirectlyHandlingTransaction(), Java_android_os_Binder_restoreCallingIdentity()

### Community 100 - "100-apk-session.sh"
Cohesion: 0.50
Nodes (3): LIBSEAT_BACKEND, 100-apk-session.sh script, XDG_RUNTIME_DIR

### Community 104 - "properties.rs"
Cohesion: 0.31
Nodes (6): HOST_PROFILE, Java_android_os_SystemProperties_native_1get_1boolean__Ljava_lang_String_2Z(), Java_android_os_SystemProperties_native_1get_1int__Ljava_lang_String_2I(), Java_android_os_SystemProperties_native_1get__Ljava_lang_String_2Ljava_lang_String_2(), Java_org_archtv_apkruntime_HostProfile_nativeInitialize(), property()

### Community 105 - "Port del framework original: primer cierre de compilación"
Cohesion: 0.22
Nodes (8): Despacho y semántica originales, Enlace JNI ya probado, Port del framework original: primer cierre de compilación, Recursos nativos originales en Linux, Referencia de compilación, Resources público original, Resultado y siguiente frontera, Uso en el runtime APK

### Community 107 - "Contrato experimental del runtime APK"
Cohesion: 0.25
Nodes (7): Canal de prueba, Contrato experimental del runtime APK, Datos y fallos, Evidencia y aceptación, Integración actual del principal AOSP, Métricas de ventana, Proceso y entradas

### Community 108 - "Primer runtime APK: ART y API mínima"
Cohesion: 0.50
Nodes (3): Construcción y prueba, Límites actuales, Primer runtime APK: ART y API mínima

### Community 109 - "NativeQueueProbe.java"
Cohesion: 0.17
Nodes (3): NativeQueueProbe, Runnable, ResourcesProbe

### Community 112 - "Port selectivo del framework original a Linux"
Cohesion: 0.20
Nodes (9): Base de estudio fijada, Fronteras concretas, Integración en la APK, JNI Linux verificado, Port selectivo del framework original a Linux, Primer conjunto original compilado, Primer despacho original, Recursos nativos originales en Linux (+1 more)

### Community 113 - ".view"
Cohesion: 0.13
Nodes (6): Main, Runnable, Runnable, Runnable, Runnable, UiShutdown

### Community 115 - "clock"
Cohesion: 0.45
Nodes (8): clock(), Java_android_os_SystemClock_currentThreadTimeMicro(), Java_android_os_SystemClock_currentThreadTimeMillis(), Java_android_os_SystemClock_currentTimeMicro(), Java_android_os_SystemClock_elapsedRealtime(), Java_android_os_SystemClock_elapsedRealtimeNanos(), Java_android_os_SystemClock_uptimeMillis(), Java_android_os_SystemClock_uptimeNanos()

### Community 118 - "MessageQueue original: enlace JNI Linux en Rust"
Cohesion: 0.40
Nodes (4): Fuentes originales y adaptación, MessageQueue original: enlace JNI Linux en Rust, Pruebas verificadas, Puerta que sigue abierta

### Community 121 - "Métricas de Resources y ventana Wayland"
Cohesion: 0.40
Nodes (4): Evidencia, Métricas de Resources y ventana Wayland, Pendientes, Sincronización de las capturas

### Community 124 - "android.rs"
Cohesion: 0.24
Nodes (6): CONTRACT_VERSION, InstallPolicy, NewOnly, Replace, InstallReceipt, ProviderError

### Community 125 - "Handler y Looper originales ejecutan mensajes en Linux"
Cohesion: 0.50
Nodes (3): Handler y Looper originales ejecutan mensajes en Linux, Implementación y fronteras, Pruebas y evidencia

### Community 128 - "Abi"
Cohesion: 0.29
Nodes (6): Abi, Arm64V8a, ArmeabiV7a, X86, X86_64, ProviderInfo

### Community 129 - "AppId"
Cohesion: 0.33
Nodes (3): AppId, identity_rejects_commands_and_keeps_android_profiles_distinct(), LaunchReceipt

### Community 130 - "RuntimeStatus"
Cohesion: 0.29
Nodes (6): BootState, Completed, Starting, Unknown, RuntimeStatus, android_status_label()

### Community 131 - "La APK usa el Looper principal original de AOSP"
Cohesion: 0.40
Nodes (4): Ensamblado y ejecución, Evidencia, Hilo y cierre, La APK usa el Looper principal original de AOSP

### Community 132 - "Capability"
Cohesion: 0.33
Nodes (6): Capability, ForceStop, InstallApk, Launch, ListApps, Suspend

### Community 134 - "winit.rs"
Cohesion: 0.10
Nodes (4): main(), dimensions(), main(), init()

### Community 135 - "Port nativo de recursos de AOSP a Linux"
Cohesion: 0.33
Nodes (5): Comprobación y límites, Fuentes y construcción, Integración en el contador, Port nativo de recursos de AOSP a Linux, Puente JNI sobre ART

### Community 138 - "AppState"
Cohesion: 0.40
Nodes (5): App, AppState, Running, Stopped, Unknown

## Knowledge Gaps
- **106 isolated node(s):** `archtv-aosp-linux`, `archtv-apk-host`, `archtv-compositor`, `Home`, `Resume` (+101 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 614 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **54 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TvCompositor` connect `TvCompositor` to `xdg_shell.rs`, `winit.rs`, `mod.rs`, `input.rs`, `drm.rs`, `session.rs`, `.process_input_event`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Client` (e.g. with `Backend` and `Node`) actually correct?**
  _`Client` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `archtv-aosp-linux`, `archtv-apk-host`, `archtv-compositor` to the rest of the system?**
  _106 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `worker.rs` be split into smaller, more focused modules?**
  _Cohesion score 0.062146892655367235 - nodes in this community are weakly interconnected._
- **Why does `Client` connect `Client` to `Renderer`, `archtv-android/src/lib.rs`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Should `resources-jni.cpp` be split into smaller, more focused modules?**
  _Cohesion score 0.09954751131221719 - nodes in this community are weakly interconnected._
- **Should `Client` be split into smaller, more focused modules?**
  _Cohesion score 0.06479081821547575 - nodes in this community are weakly interconnected._