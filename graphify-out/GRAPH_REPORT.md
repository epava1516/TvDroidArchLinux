# Graph Report - repositorio-principal  (2026-10-30)

## Corpus Check
- 75 files · ~34,055 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 5)

## Summary
- 800 nodes · 1415 edges · 67 communities (34 shown, 33 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 4 edges (avg confidence: 0.76)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bded4a5c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- model.rs
- runtime.rs
- Client
- worker.rs
- TvCompositor
- xdg_shell.rs
- input-probe.py
- mod.rs
- input.rs
- drm.rs
- compositor.rs
- winit.rs
- Backend
- FocusStack<T>
- Roadmap · Arch TV nativo en Rust
- session.rs
- README.md
- Estado real del proyecto
- .shell
- Referencias Fire TV para Arch TV
- common.sh
- 72-anvil-smoke.sh
- 82-rust-smoke.sh
- Shell Rust: prototipo de dibujo
- Base actual y herramientas conservadas
- Desarrollo del compositor Rust
- Estudio de Smithay y Anvil
- 68-graphify.sh
- graphify.sh
- Arquitectura objetivo
- Arch TV · compositor propio para televisión
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
- archtv-compositor/src/main.rs
- Model
- 89-shell-resolutions.sh
- Action
- Key
- Page
- 87-shell-session.sh
- 88-shell-smoke.sh
- Canvas
- layout.rs
- Dirección futura: entorno APK propio sobre Linux
- REFERENCIAS-FIRE-TV.md
- 90-android-session.sh
- 93-android-shell-session.sh
- 91-android-client.sh
- 92-android-boot-probe.sh
- 94-android-media-probe.sh

## God Nodes (most connected - your core abstractions)
1. `State` - 54 edges
2. `Client` - 48 edges
3. `TvCompositor` - 45 edges
4. `Model` - 29 edges
5. `Action` - 20 edges
6. `start()` - 20 edges
7. `Backend` - 15 edges
8. `Page` - 15 edges
9. `Key` - 15 edges
10. `Roadmap · Arch TV nativo en Rust` - 15 edges

## Surprising Connections (you probably didn't know these)
- `start()` --calls--> `data_directories()`  [INFERRED]
  crates/archtv-shell/src/worker.rs → crates/archtv-core/src/desktop.rs
- `State` --references--> `Settings`  [INFERRED]
  crates/archtv-shell/src/runtime.rs → crates/archtv-shell/src/model.rs
- `init()` --references--> `TvCompositor`  [EXTRACTED]
  crates/archtv-compositor/src/drm.rs → crates/archtv-compositor/src/state.rs
- `start()` --references--> `TvCompositor`  [EXTRACTED]
  crates/archtv-compositor/src/session.rs → crates/archtv-compositor/src/state.rs
- `init()` --references--> `TvCompositor`  [EXTRACTED]
  crates/archtv-compositor/src/winit.rs → crates/archtv-compositor/src/state.rs

## Import Cycles
- None detected.

## Communities (67 total, 33 thin omitted)

### Community 0 - "model.rs"
Cohesion: 0.18
Nodes (9): ContextAction, Cancel, Favorite, Hide, Left, Right, KEYBOARD, MENU_ITEMS (+1 more)

### Community 1 - "runtime.rs"
Cohesion: 0.07
Nodes (3): control_fd(), run(), State

### Community 3 - "worker.rs"
Cohesion: 0.07
Nodes (32): Application, collect(), data_directories(), discover(), exec_keeps_arguments_and_shell_metacharacters_literal(), executable(), expand_exec(), locale_hidden_and_desktop_sections_are_respected() (+24 more)

### Community 4 - "TvCompositor"
Cohesion: 0.08
Nodes (3): TvCompositor, ClientState, TvCompositor

### Community 6 - "input-probe.py"
Cohesion: 0.08
Nodes (16): key(), text(), wait_for(), event(), wait_for(), chunk(), event(), audio() (+8 more)

### Community 8 - "input.rs"
Cohesion: 0.09
Nodes (5): Shortcut, Exit, Home, Resume, Vt

### Community 12 - "Backend"
Cohesion: 0.20
Nodes (3): Backend, init(), Result

### Community 13 - "FocusStack<T>"
Cohesion: 0.30
Nodes (4): FocusStack, FocusStack<T>, home_returns_without_destroying_app_and_close_restores_focus(), repeated_activation_does_not_duplicate_a_window()

### Community 14 - "Roadmap · Arch TV nativo en Rust"
Cohesion: 0.13
Nodes (15): Alcance inicial, Evolución posterior: AOSP propio y ejecución de APK, H0 · Limpieza y base documental, H1 · Rust y Anvil como laboratorio, H2 · Compositor mínimo propio, H3 · Salida directa y decisión de renderizado, H4 · Comportamiento de televisión y sesión, H5 · Interfaz Rust con referencia Fire TV 2026 (+7 more)

### Community 15 - "session.rs"
Cohesion: 0.38
Nodes (3): Result, start(), Supervisor

### Community 17 - "Estado real del proyecto"
Cohesion: 0.14
Nodes (14): Comprobaciones y evidencia, Copia previa, Desarrollo interactivo y seguimiento, Dirección actual, Estado de Android y gráficos, Estado real del proyecto, H1 comprobado, H2 comprobado: compositor propio (+6 more)

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

### Community 23 - "Shell Rust: prototipo de dibujo"
Cohesion: 0.33
Nodes (6): Composición medida, Decisión provisional, Primer resultado del renderer optimizado, Reproducción, Shell Rust: interfaz y mediciones, Validación interactiva

### Community 24 - "Base actual y herramientas conservadas"
Cohesion: 0.33
Nodes (6): Android existente, Base actual y herramientas conservadas, Desarrollo propio disponible, Diagnóstico, Manifiestos, Scripts de sistema

### Community 25 - "Desarrollo del compositor Rust"
Cohesion: 0.29
Nodes (7): Construcción y comprobaciones, Desarrollo del compositor Rust, Ensayo del shell interactivo, Ensayo directo en VM, Límites actuales, Política y supervisión, Resoluciones del shell real

### Community 26 - "Estudio de Smithay y Anvil"
Cohesion: 0.40
Nodes (5): Estudio de Smithay y Anvil, Mapa de lectura, Qué no resuelve Smithay automáticamente, Revisión de referencia, Riesgo gráfico que debe resolverse primero

### Community 27 - "68-graphify.sh"
Cohesion: 0.40
Nodes (4): GRAPHIFY_BACKEND, GRAPHIFY_MAX_WORKERS, PYTHONHASHSEED, 68-graphify.sh script

### Community 28 - "graphify.sh"
Cohesion: 0.40
Nodes (4): GRAPHIFY_BACKEND, GRAPHIFY_MAX_WORKERS, PYTHONHASHSEED, graphify.sh script

### Community 29 - "Arquitectura objetivo"
Cohesion: 0.40
Nodes (5): Arquitectura objetivo, Decisiones iniciales, Dependencias compartidas, Entrada y control, Evolución del entorno Android

### Community 30 - "Arch TV · compositor propio para televisión"
Cohesion: 0.50
Nodes (4): Arch TV · compositor propio para televisión, Documentación principal, Herramientas disponibles, Laboratorio H1

### Community 31 - "archtv-core"
Cohesion: 0.67
Nodes (3): archtv-compositor, archtv-core, archtv-shell

### Community 50 - "Model"
Cohesion: 0.22
Nodes (5): app(), context_order_hide_restore_and_row_focus_survive_navigation(), keyboard_and_physical_search_agree_and_back_is_bounded(), Model, navigation_filters_and_banner_use_real_application_sets()

### Community 51 - "89-shell-resolutions.sh"
Cohesion: 0.20
Nodes (8): EGL_PLATFORM, GALLIUM_DRIVER, LIBGL_ALWAYS_SOFTWARE, 89-shell-resolutions.sh script, XDG_CONFIG_HOME, XDG_DATA_DIRS, XDG_DATA_HOME, XDG_RUNTIME_DIR

### Community 52 - "Action"
Cohesion: 0.17
Nodes (11): Action, AndroidStart, AndroidStop, Launch, Mute, Quit, Refresh, Resume (+3 more)

### Community 53 - "Key"
Cohesion: 0.20
Nodes (10): Key, Back, Backspace, Character, Down, Enter, Left, Menu (+2 more)

### Community 54 - "Page"
Cohesion: 0.18
Nodes (9): Page, Android, Apps, Home, Linux, Menu, Recent, Search (+1 more)

### Community 55 - "87-shell-session.sh"
Cohesion: 0.50
Nodes (3): DBUS_SESSION_BUS_ADDRESS, LIBSEAT_BACKEND, 87-shell-session.sh script

### Community 58 - "layout.rs"
Cohesion: 0.14
Nodes (13): APP_HEIGHT, APP_STEP, APP_WIDTH, APP_Y, BANNER_HEIGHT, BANNER_Y, FEATURE_HEIGHT, FEATURE_STEP (+5 more)

### Community 59 - "Dirección futura: entorno APK propio sobre Linux"
Cohesion: 0.40
Nodes (5): Arquitectura que se investigará, Dirección futura: entorno APK propio sobre Linux, Etapas y pruebas de salida, Qué significa ejecutar APK de forma nativa, Recursos y decisiones pendientes

### Community 61 - "90-android-session.sh"
Cohesion: 0.50
Nodes (3): DBUS_SESSION_BUS_ADDRESS, LIBSEAT_BACKEND, 90-android-session.sh script

### Community 62 - "93-android-shell-session.sh"
Cohesion: 0.50
Nodes (3): DBUS_SESSION_BUS_ADDRESS, LIBSEAT_BACKEND, 93-android-shell-session.sh script

## Knowledge Gaps
- **69 isolated node(s):** `archtv-compositor`, `Home`, `Resume`, `Exit`, `TvCompositor` (+64 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 319 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **33 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TvCompositor` connect `TvCompositor` to `session.rs`, `xdg_shell.rs`, `mod.rs`, `input.rs`, `drm.rs`, `compositor.rs`, `winit.rs`, `Backend`, `session.rs`, `archtv-compositor/src/main.rs`?**
  _High betweenness centrality (0.213) - this node is a cross-community bridge._
- **What connects `archtv-compositor`, `Home`, `Resume` to the rest of the system?**
  _69 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `runtime.rs` be split into smaller, more focused modules?**
  _Cohesion score 0.07042253521126761 - nodes in this community are weakly interconnected._
- **Why does `Event` connect `worker.rs` to `input.rs`, `runtime.rs`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Should `Client` be split into smaller, more focused modules?**
  _Cohesion score 0.07080745341614907 - nodes in this community are weakly interconnected._
- **Why does `Model` connect `Model` to `model.rs`, `runtime.rs`, `worker.rs`, `.shell`, `Action`, `Page`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Should `worker.rs` be split into smaller, more focused modules?**
  _Cohesion score 0.07184325108853411 - nodes in this community are weakly interconnected._