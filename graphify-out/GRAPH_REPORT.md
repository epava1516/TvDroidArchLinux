# Graph Report - repositorio-principal  (2026-10-30)

## Corpus Check
- 136 files · ~54,230 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 5, .xml 2, .apk 1)

## Summary
- 1266 nodes · 2352 edges · 107 communities (58 shown, 49 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 39 edges (avg confidence: 0.81)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f93d77ce`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Model
- runtime.rs
- Client
- worker.rs
- TvCompositor
- xdg_shell.rs
- mod.rs
- input.rs
- drm.rs
- compositor.rs
- session.rs
- winit.rs
- FocusStack<T>
- Roadmap · Arch TV nativo en Rust
- 95-kernel-lts.sh
- json
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
- argparse
- .process_input_event
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
- RuntimeStatus
- ErrorKind
- 89-shell-resolutions.sh
- android.rs
- ClientState
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
- AndroidProvider
- 94-android-media-probe.sh
- Cuelgue completo de la VM durante H6
- Arch TV · compositor propio para televisión
- Paquetes Arch TV en preparación
- 97-package-source.sh
- Abi
- AppId
- Contrato Android A0 · borrador v1
- 99-iso-build.sh
- Capability
- AppState
- archtv-android/src/lib.rs
- apk_inventory.py
- archtv-compositor/src/main.rs
- Context
- tv-ui-probe.py
- ROADMAP.md
- SessionState
- Client
- ApkResources
- Capa de compatibilidad APK propia sobre Linux
- Capa de compatibilidad APK propia sobre Linux
- APK mínima: contador
- RuntimeProbe
- APK original en el compositor propio
- ART host para la capa APK
- Canvas
- .onClick
- Activity
- .view
- 100-apk-session.sh
- 101-apk-smoke.sh
- ApkResources.java
- archtv-apk-host
- View
- Contrato experimental del runtime APK
- Primer runtime APK: ART y API mínima

## God Nodes (most connected - your core abstractions)
1. `State` - 54 edges
2. `Client` - 48 edges
3. `Client` - 45 edges
4. `TvCompositor` - 45 edges
5. `Model` - 29 edges
6. `Action` - 20 edges
7. `start()` - 19 edges
8. `Activity` - 17 edges
9. `Context` - 16 edges
10. `ApkResources` - 16 edges

## Surprising Connections (you probably didn't know these)
- `MainActivity` --inherits--> `Activity`  [EXTRACTED]
  fixtures/apk/counter/src/org/archtv/probe/MainActivity.java → runtime/apk/java/android/app/Activity.java
- `MainActivity` --references--> `SharedPreferences`  [EXTRACTED]
  fixtures/apk/counter/src/org/archtv/probe/MainActivity.java → runtime/apk/java/android/content/SharedPreferences.java
- `MainActivity` --references--> `TextView`  [EXTRACTED]
  fixtures/apk/counter/src/org/archtv/probe/MainActivity.java → runtime/apk/java/android/widget/TextView.java
- `Client` --references--> `Backend`  [INFERRED]
  crates/archtv-apk-host/src/main.rs → crates/archtv-apk-host/src/backend.rs
- `Client` --references--> `Node`  [INFERRED]
  crates/archtv-apk-host/src/main.rs → crates/archtv-apk-host/src/model.rs

## Import Cycles
- None detected.

## Communities (107 total, 49 thin omitted)

### Community 0 - "Model"
Cohesion: 0.06
Nodes (38): Application, Action, AndroidStart, AndroidStop, Launch, Mute, Quit, Refresh (+30 more)

### Community 1 - "runtime.rs"
Cohesion: 0.07
Nodes (13): Key, Back, Backspace, Character, Down, Enter, Left, Menu (+5 more)

### Community 3 - "worker.rs"
Cohesion: 0.08
Nodes (29): collect(), data_directories(), discover(), exec_keeps_arguments_and_shell_metacharacters_literal(), executable(), expand_exec(), locale_hidden_and_desktop_sections_are_respected(), parse_entry() (+21 more)

### Community 8 - "input.rs"
Cohesion: 0.09
Nodes (5): Shortcut, Exit, Home, Resume, Vt

### Community 9 - "drm.rs"
Cohesion: 0.08
Nodes (4): Backend, init(), Result, Scanout

### Community 11 - "session.rs"
Cohesion: 0.21
Nodes (3): Result, start(), Supervisor

### Community 13 - "FocusStack<T>"
Cohesion: 0.30
Nodes (4): FocusStack, FocusStack<T>, home_returns_without_destroying_app_and_close_restores_focus(), repeated_activation_does_not_duplicate_a_window()

### Community 14 - "Roadmap · Arch TV nativo en Rust"
Cohesion: 0.13
Nodes (15): Alcance inicial, Evolución A · compatibilidad APK mínima sobre Linux, H0 · Limpieza y base documental, H1 · Rust y Anvil como laboratorio, H2 · Compositor mínimo propio, H3 · Salida directa y decisión de renderizado, H4 · Comportamiento de televisión y sesión, H5 · Interfaz Rust con referencia Fire TV 2026 (+7 more)

### Community 17 - "Estudio de Smithay y Anvil"
Cohesion: 0.40
Nodes (5): Estudio de Smithay y Anvil, Mapa de lectura, Qué no resuelve Smithay automáticamente, Revisión de referencia, Riesgo gráfico que debe resolverse primero

### Community 18 - "Roadmap A · compatibilidad APK mínima sobre Linux"
Cohesion: 0.29
Nodes (7): Corrección del enfoque anterior, DEX de la APK ejecutado con API mínima, Fixture disponible, Primer motor probado, Próximo experimento, Roadmap A · compatibilidad APK mínima sobre Linux, Ventana y entrada verificadas; dirección del port

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

### Community 29 - "argparse"
Cohesion: 0.16
Nodes (3): radio(), inspect(), run()

### Community 31 - "archtv-core"
Cohesion: 0.67
Nodes (4): archtv-android, archtv-compositor, archtv-core, archtv-shell

### Community 49 - "RuntimeStatus"
Cohesion: 0.29
Nodes (6): BootState, Completed, Starting, Unknown, RuntimeStatus, android_status_label()

### Community 50 - "ErrorKind"
Cohesion: 0.18
Nodes (11): ErrorKind, BackendFailure, Conflict, IncompatibleAbi, InvalidRequest, NotFound, NotReady, PermissionDenied (+3 more)

### Community 51 - "89-shell-resolutions.sh"
Cohesion: 0.20
Nodes (8): EGL_PLATFORM, GALLIUM_DRIVER, LIBGL_ALWAYS_SOFTWARE, 89-shell-resolutions.sh script, XDG_CONFIG_HOME, XDG_DATA_DIRS, XDG_DATA_HOME, XDG_RUNTIME_DIR

### Community 52 - "android.rs"
Cohesion: 0.24
Nodes (6): CONTRACT_VERSION, InstallPolicy, NewOnly, Replace, InstallReceipt, ProviderError

### Community 55 - "87-shell-session.sh"
Cohesion: 0.50
Nodes (3): DBUS_SESSION_BUS_ADDRESS, LIBSEAT_BACKEND, 87-shell-session.sh script

### Community 58 - "layout.rs"
Cohesion: 0.14
Nodes (13): APP_HEIGHT, APP_STEP, APP_WIDTH, APP_Y, BANNER_HEIGHT, BANNER_Y, FEATURE_HEIGHT, FEATURE_STEP (+5 more)

### Community 59 - "time"
Cohesion: 0.18
Nodes (9): key(), text(), wait_for(), key(), wait(), event(), wait_for(), chunk() (+1 more)

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

### Community 72 - "Abi"
Cohesion: 0.29
Nodes (6): Abi, Arm64V8a, ArmeabiV7a, X86, X86_64, ProviderInfo

### Community 73 - "AppId"
Cohesion: 0.33
Nodes (3): AppId, identity_rejects_commands_and_keeps_android_profiles_distinct(), LaunchReceipt

### Community 74 - "Contrato Android A0 · borrador v1"
Cohesion: 0.25
Nodes (7): Aceptación A0, Adaptador de estado implementado, Contrato anterior de proveedores Android · borrador sin congelar, Identidad y negociación, Operaciones y resultados, Plazos y errores, Transporte y adaptación pendientes

### Community 76 - "Capability"
Cohesion: 0.33
Nodes (6): Capability, ForceStop, InstallApk, Launch, ListApps, Suspend

### Community 77 - "AppState"
Cohesion: 0.40
Nodes (5): App, AppState, Running, Stopped, Unknown

### Community 78 - "archtv-android/src/lib.rs"
Cohesion: 0.06
Nodes (10): command_deadline_and_output_limit_do_not_wait_for_pipe_eof(), drain(), error(), Process, run(), status_requires_exact_boot_value_and_rejects_stale_boot_for_stopped_session(), unsupported(), Waydroid (+2 more)

### Community 79 - "apk_inventory.py"
Cohesion: 0.21
Nodes (6): dex_inventory(), string(), table(), uint(), execute(), kill_group()

### Community 80 - "archtv-compositor/src/main.rs"
Cohesion: 0.18
Nodes (3): main(), dimensions(), main()

### Community 81 - "Context"
Cohesion: 0.13
Nodes (4): Context, Button, LinearLayout, TextView

### Community 82 - "tv-ui-probe.py"
Cohesion: 0.31
Nodes (7): audio(), event(), key(), state(), text(), volume(), wait_for()

### Community 84 - "SessionState"
Cohesion: 0.33
Nodes (6): SessionState, Running, Starting, Stopped, Suspended, Unknown

### Community 87 - "Capa de compatibilidad APK propia sobre Linux"
Cohesion: 0.40
Nodes (5): Alcance y recursos, APK propia preparada, Capa de compatibilidad APK propia sobre Linux, Primer estudio implementado, Qué se debe demostrar

### Community 88 - "Capa de compatibilidad APK propia sobre Linux"
Cohesion: 0.25
Nodes (8): Alcance y recursos, APK propia preparada, ART host ejecuta DEX en Linux, Capa de compatibilidad APK propia sobre Linux, La APK propia ejecuta sus callbacks en Linux, La APK tiene ventana Wayland y entrada real de la pila Linux, Primer estudio implementado, Qué se debe demostrar

### Community 89 - "APK mínima: contador"
Cohesion: 0.50
Nodes (3): APK mínima: contador, Construcción, Prueba que debe pasar la futura capa

### Community 92 - "RuntimeProbe"
Cohesion: 0.39
Nodes (3): Increment, Operation, RuntimeProbe

### Community 94 - "APK original en el compositor propio"
Cohesion: 0.50
Nodes (3): APK original en el compositor propio, Límites y siguiente dirección, Prueba verificada

### Community 95 - "ART host para la capa APK"
Cohesion: 0.40
Nodes (4): ART host para la capa APK, Fuentes y alcance, Pruebas separadas, Resultado del primer experimento

### Community 96 - "Canvas"
Cohesion: 0.12
Nodes (4): Message, Node, Renderer, Canvas

### Community 97 - ".onClick"
Cohesion: 0.16
Nodes (4): Editor, SharedPreferences, IntPreferences, Transaction

### Community 100 - "100-apk-session.sh"
Cohesion: 0.50
Nodes (3): LIBSEAT_BACKEND, 100-apk-session.sh script, XDG_RUNTIME_DIR

### Community 104 - "View"
Cohesion: 0.22
Nodes (4): MainActivity, OnClickListener, View, ViewGroup

### Community 107 - "Contrato experimental del runtime APK"
Cohesion: 0.33
Nodes (5): Canal de prueba, Contrato experimental del runtime APK, Datos y fallos, Evidencia y aceptación, Proceso y entradas

### Community 108 - "Primer runtime APK: ART y API mínima"
Cohesion: 0.50
Nodes (3): Construcción y prueba, Límites actuales, Primer runtime APK: ART y API mínima

## Knowledge Gaps
- **103 isolated node(s):** `archtv-apk-host`, `archtv-compositor`, `Home`, `Resume`, `Exit` (+98 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 482 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **49 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TvCompositor` connect `TvCompositor` to `xdg_shell.rs`, `mod.rs`, `input.rs`, `drm.rs`, `compositor.rs`, `session.rs`, `winit.rs`, `archtv-compositor/src/main.rs`, `.process_input_event`?**
  _High betweenness centrality (0.120) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Client` (e.g. with `Backend` and `Node`) actually correct?**
  _`Client` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `archtv-apk-host`, `archtv-compositor`, `Home` to the rest of the system?**
  _103 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Model` be split into smaller, more focused modules?**
  _Cohesion score 0.05860805860805861 - nodes in this community are weakly interconnected._
- **Why does `Event` connect `worker.rs` to `input.rs`, `runtime.rs`, `Model`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Should `runtime.rs` be split into smaller, more focused modules?**
  _Cohesion score 0.06664198445020363 - nodes in this community are weakly interconnected._
- **Why does `Client` connect `Client` to `Client`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._