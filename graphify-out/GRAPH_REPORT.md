# Graph Report - selinux-permissive-boot-20261031  (2026-10-31)

## Corpus Check
- 316 files · ~272,434 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 23 file(s) not represented in the graph (top: .xml 8, (none) 6, .patch 3)

## Summary
- 2886 nodes · 5510 edges · 222 communities (121 shown, 101 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 95 edges (avg confidence: 0.83)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c03ad34c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- worker.rs
- resources-jni.cpp
- Client
- .shell
- TvCompositor
- xdg_shell.rs
- LinuxWindowService
- mod.rs
- drm.rs
- archtv-aosp-linux/src/lib.rs
- session.rs
- json
- LinuxContext
- Roadmap · Arch TV nativo en Rust
- 95-kernel-lts.sh
- lock_release_manifest.py
- Estudio de Smithay y Anvil
- Roadmap A · compatibilidad APK mínima sobre Linux
- Referencias Fire TV para Arch TV
- common.sh
- 72-anvil-smoke.sh
- 82-rust-smoke.sh
- Shell Rust: interfaz y mediciones
- re
- Desarrollo del compositor Rust
- Arquitectura objetivo
- 68-graphify.sh
- graphify.sh
- properties.rs
- .current
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
- Intent
- 89-shell-resolutions.sh
- Constructor de View original en Linux
- archtv-shell/src/model.rs
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
- LinuxShutdownSink
- 94-android-media-probe.sh
- Cuelgue completo de la VM durante H6
- Arch TV · compositor propio para televisión
- Paquetes Arch TV en preparación
- 97-package-source.sh
- .onClick
- Contrato Android A0 · borrador v1
- 99-iso-build.sh
- View
- Client
- Waydroid
- pathlib
- Reference
- Checkpoint y recuperación
- aosp-critical-host/native-probe.cpp
- ROADMAP.md
- Renderer
- runtime.rs
- Índice de evidencias
- Capa de compatibilidad APK propia sobre Linux
- Capa de compatibilidad APK propia sobre Linux
- APK mínima: contador
- .main
- .process_input_event
- RuntimeProbe
- APK original en el compositor propio
- ART host para la capa APK
- hashlib
- Constructor original de View con recursos del APK
- Activity
- identity.rs
- 100-apk-session.sh
- 101-apk-smoke.sh
- audit-service-profiles.cpp
- archtv-apk-host
- prepare_factory_inputs.py
- Port del framework original: primer cierre de compilación
- QueueLinkProbe
- Contrato experimental del runtime APK
- Primer runtime APK: ART y API mínima
- NativeQueueProbe.java
- UnsupportedAppUsage.java
- Inicio del port de vistas originales
- Port selectivo del framework original a Linux
- View
- clock
- ContextAction
- .metafactory
- MessageQueue original: enlace JNI Linux en Rust
- archtv-aosp-linux
- Contrato vigente de ejecución APK
- Métricas de Resources y ventana Wayland
- FocusStack<T>
- JNI_OnLoad
- src/native_process.rs
- Handler y Looper originales ejecutan mensajes en Linux
- tests/native_process.rs
- Backend
- Java_android_os_Binder_getNativeBBinderHolder
- desktop.rs
- ThrowableLogProbe.java
- La APK usa el Looper principal original de AOSP
- ApkMetadata
- Main.java
- duration
- Port nativo de recursos de AOSP a Linux
- LinuxChildReaper
- ApkResources.java
- CriticalHostProbe
- ViewLinkageProbe
- Bootstrap de servicios originales sobre Linux
- tracing.rs
- Context y Application originales sobre Linux
- Política de animación original y contexto visual
- Capability
- .state
- extract_platform_modules.py
- RenderNodeProbe
- Medida de View original y siguiente frontera de layout
- context-metrics/README.md
- archtv-android/src/lib.rs
- LinuxServiceRegistry
- Interpoladores originales HWUI ejecutados en ART
- NativeInterpolatorsProbe
- AndroidProvider
- Log original de AOSP con JNI Linux
- Recursos de sistema AOSP junto a los del APK
- android.rs
- dex_inventory
- Action
- verify_counter_headless.py
- Consultas IWindowManager respaldadas por Wayland
- ErrorKind
- Port gráfico original: frontera RenderNode
- Adaptación tipada de CriticalNative a funciones host HWUI
- build_skia_host.py
- Traducción ARM · investigación R6 separada
- Cliente de accesibilidad original: contratos y frontera Binder
- ApplicationInfo original y metadatos reales de APK
- Contrato vigente · AOSP Android 16 QPR2
- Perfil JNI original de construcción y propiedades RenderNode
- BootState
- Page
- AuditedSectionParser
- Holder Binder original en ART/Linux
- Arquitectura vigente · A16-QPR2-1
- FrameworkSpaceProbe
- ClientState
- ClockNativeProbe.java
- .initialize
- Log original con excepciones y líneas largas
- Matriz de aplicaciones reales
- Roadmap A · plataforma APK general sobre Linux
- check_host_security.py
- HostSecurityReporting
- SessionState
- Puerta vigente: Binder privado y política del Linux anfitrión
- Historial conservado · no es el estado vigente
- patches/README.md

## God Nodes (most connected - your core abstractions)
1. `LinuxWindowService` - 140 edges
2. `LinuxContext` - 110 edges
3. `Estado actual y punto de entrada` - 60 edges
4. `State` - 54 edges
5. `Arquitectura vigente · A16-QPR2-1` - 50 edges
6. `Client` - 48 edges
7. `Client` - 47 edges
8. `TvCompositor` - 45 edges
9. `Model` - 29 edges
10. `LinuxServiceRegistry` - 24 edges

## Surprising Connections (you probably didn't know these)
- `Procedencia y construcción` --references--> `Reference`  [INFERRED]
  docs/AOSP-RESOURCES-PUBLICO.md → runtime/aosp/compile-stubs/java/lang/ref/Reference.java
- `main()` --calls--> `read()`  [INFERRED]
  runtime/aosp/native/linux-property-worker.cpp → fixtures/aosp-critical-host/native-probe.cpp
- `probe()` --calls--> `read()`  [INFERRED]
  tools/aosp/property_area_probe.c → fixtures/aosp-critical-host/native-probe.cpp
- `start()` --calls--> `data_directories()`  [INFERRED]
  crates/archtv-shell/src/worker.rs → crates/archtv-core/src/desktop.rs
- `MainActivity` --references--> `SharedPreferences`  [EXTRACTED]
  fixtures/apk/counter/src/org/archtv/probe/MainActivity.java → runtime/apk/java/android/content/SharedPreferences.java

## Import Cycles
- None detected.

## Communities (222 total, 101 thin omitted)

### Community 0 - "worker.rs"
Cohesion: 0.10
Nodes (23): RuntimeStatus, Settings, android_status_label(), decode_icon(), decode_wallpaper(), downgrade_does_not_overwrite_newer_settings(), Event, Icon (+15 more)

### Community 1 - "resources-jni.cpp"
Cohesion: 0.12
Nodes (25): ascii16(), fail(), guard(), Java_android_content_res_ApkAssets_nativeDestroy(), Java_android_content_res_ApkAssets_nativeGetStringBlock(), Java_android_content_res_ApkAssets_nativeLoad(), Java_android_content_res_AssetManager_nativeCreate(), Java_android_content_res_AssetManager_nativeDestroy() (+17 more)

### Community 5 - "xdg_shell.rs"
Cohesion: 0.06
Nodes (3): TvCompositor, handle_commit(), TvCompositor

### Community 10 - "archtv-aosp-linux/src/lib.rs"
Cohesion: 0.05
Nodes (33): guard(), Java_android_os_MessageQueue_nativeDestroy(), Java_android_os_MessageQueue_nativeInit(), Java_android_os_MessageQueue_nativeIsPolling(), Java_android_os_MessageQueue_nativePollOnce(), Java_android_os_MessageQueue_nativeSetFileDescriptorEvents(), Java_android_os_MessageQueue_nativeWake(), lookup() (+25 more)

### Community 11 - "session.rs"
Cohesion: 0.19
Nodes (3): Result, start(), Supervisor

### Community 12 - "json"
Cohesion: 0.08
Nodes (10): audit(), inside(), inventory(), main(), fetch(), fetch_file(), main(), main() (+2 more)

### Community 14 - "Roadmap · Arch TV nativo en Rust"
Cohesion: 0.12
Nodes (17): Alcance inicial, Evolución A · compatibilidad APK mínima sobre Linux, H0 · Limpieza y base documental, H1 · Rust y Anvil como laboratorio, H2 · Compositor mínimo propio, H3 · Salida directa y decisión de renderizado, H4 · Comportamiento de televisión y sesión, H5 · Interfaz Rust con referencia Fire TV 2026 (+9 more)

### Community 16 - "lock_release_manifest.py"
Cohesion: 0.33
Nodes (4): main(), parse_ref(), resolve_project(), sha()

### Community 17 - "Estudio de Smithay y Anvil"
Cohesion: 0.40
Nodes (5): Estudio de Smithay y Anvil, Mapa de lectura, Qué no resuelve Smithay automáticamente, Revisión de referencia, Riesgo gráfico que debe resolverse primero

### Community 18 - "Roadmap A · compatibilidad APK mínima sobre Linux"
Cohesion: 0.10
Nodes (20): Bootstrap original aislado · 2026-10-30, Corrección del enfoque anterior, DEX de la APK ejecutado con API mínima, Entregables actuales de la reconducción, Fixture disponible, Framework modular original · 2026-10-30, La APK ya usa el principal original, Primer experimento (histórico) (+12 more)

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

### Community 24 - "re"
Cohesion: 0.14
Nodes (15): audit_kernel_contract(), classes(), compile_policy(), compose(), digest(), forms(), keyword(), main() (+7 more)

### Community 25 - "Desarrollo del compositor Rust"
Cohesion: 0.13
Nodes (13): Construcción y comprobaciones, Desarrollo del compositor Rust, Ensayo del shell interactivo, Ensayo directo en VM, Límites actuales, Política y supervisión, Resoluciones del shell real, Android existente (+5 more)

### Community 26 - "Arquitectura objetivo"
Cohesion: 0.08
Nodes (24): Antecedentes históricos (no son decisiones vigentes), Arquitectura anterior BASE-AOSP-1, Arquitectura objetivo anterior, Arquitecturas y aislamiento, Bionic, libhybris y servicios originales, Comparación de estrategias y mezclas actuales, Componentes, procesos y cierre mínimo, Decisiones iniciales (+16 more)

### Community 27 - "68-graphify.sh"
Cohesion: 0.40
Nodes (4): GRAPHIFY_BACKEND, GRAPHIFY_MAX_WORKERS, PYTHONHASHSEED, 68-graphify.sh script

### Community 28 - "graphify.sh"
Cohesion: 0.40
Nodes (4): GRAPHIFY_BACKEND, GRAPHIFY_MAX_WORKERS, PYTHONHASHSEED, graphify.sh script

### Community 29 - "properties.rs"
Cohesion: 0.35
Nodes (6): HOST_PROFILE, Java_android_os_SystemProperties_native_1get_1boolean__Ljava_lang_String_2Z(), Java_android_os_SystemProperties_native_1get_1int__Ljava_lang_String_2I(), Java_android_os_SystemProperties_native_1get__Ljava_lang_String_2Ljava_lang_String_2(), Java_org_archtv_apkruntime_HostProfile_nativeInitialize(), property()

### Community 30 - ".current"
Cohesion: 0.21
Nodes (3): Attached, ContextProbe, android.content.ComponentCallbacks2

### Community 31 - "archtv-core"
Cohesion: 0.67
Nodes (4): archtv-android, archtv-compositor, archtv-core, archtv-shell

### Community 51 - "89-shell-resolutions.sh"
Cohesion: 0.20
Nodes (8): EGL_PLATFORM, GALLIUM_DRIVER, LIBGL_ALWAYS_SOFTWARE, 89-shell-resolutions.sh script, XDG_CONFIG_HOME, XDG_DATA_DIRS, XDG_DATA_HOME, XDG_RUNTIME_DIR

### Community 52 - "Constructor de View original en Linux"
Cohesion: 0.50
Nodes (3): Alcance, Constructor de View original en Linux, Dependencias resueltas

### Community 53 - "archtv-shell/src/model.rs"
Cohesion: 0.17
Nodes (9): Application, app(), context_order_hide_restore_and_row_focus_survive_navigation(), KEYBOARD, keyboard_and_physical_search_agree_and_back_is_bounded(), MENU_ITEMS, Model, navigation_filters_and_banner_use_real_application_sets() (+1 more)

### Community 55 - "87-shell-session.sh"
Cohesion: 0.50
Nodes (3): DBUS_SESSION_BUS_ADDRESS, LIBSEAT_BACKEND, 87-shell-session.sh script

### Community 58 - "layout.rs"
Cohesion: 0.14
Nodes (13): APP_HEIGHT, APP_STEP, APP_WIDTH, APP_Y, BANNER_HEIGHT, BANNER_Y, FEATURE_HEIGHT, FEATURE_STEP (+5 more)

### Community 59 - "time"
Cohesion: 0.09
Nodes (20): key(), text(), wait_for(), capture_matching(), key(), wait(), wait_frame_after(), event() (+12 more)

### Community 60 - "DISTRIBUCION.md"
Cohesion: 0.33
Nodes (5): Construcción con comprobación de errores, Distribución Arch TV: perfil de laboratorio, ISO corregida construida, Login y sesión nativa desde la ISO, Primera construcción en curso y corrección detectada

### Community 61 - "90-android-session.sh"
Cohesion: 0.50
Nodes (3): DBUS_SESSION_BUS_ADDRESS, LIBSEAT_BACKEND, 90-android-session.sh script

### Community 62 - "93-android-shell-session.sh"
Cohesion: 0.50
Nodes (3): DBUS_SESSION_BUS_ADDRESS, LIBSEAT_BACKEND, 93-android-shell-session.sh script

### Community 65 - "LinuxShutdownSink"
Cohesion: 0.13
Nodes (8): close_actions(), main(), send_status(), LinuxShutdownSink, command_, installed_, oversize_, size_

### Community 67 - "Cuelgue completo de la VM durante H6"
Cohesion: 0.25
Nodes (7): Alternativa LTS preparada, Arranque LTS verificado, Continuación, Cuelgue completo de la VM durante H6, Estado después del reinicio, Evidencia guardada, Soft lockups también con LTS

### Community 68 - "Arch TV · compositor propio para televisión"
Cohesion: 0.50
Nodes (4): Arch TV · compositor propio para televisión, Documentación principal, Herramientas disponibles, Laboratorio H1

### Community 69 - "Paquetes Arch TV en preparación"
Cohesion: 0.15
Nodes (12): Compilación en entorno limpio, Fuentes y receta, Herramientas para la imagen de distribución, Inventario inicial de licencias Cargo, Paquetes Arch TV en preparación, Preferencias y recuperación entre versiones, Primera compilación e instalación comprobadas, Prueba del ciclo de paquetes preparada (+4 more)

### Community 72 - ".onClick"
Cohesion: 0.10
Nodes (5): Editor, SharedPreferences, AppEnvironment, IntPreferences, Transaction

### Community 74 - "Contrato Android A0 · borrador v1"
Cohesion: 0.25
Nodes (7): Aceptación A0, Adaptador de estado implementado, Contrato anterior de proveedores Android · borrador sin congelar, Identidad y negociación, Operaciones y resultados, Plazos y errores, Transporte y adaptación pendientes

### Community 76 - "View"
Cohesion: 0.12
Nodes (5): OnClickListener, View, ViewGroup, Button, LinearLayout

### Community 77 - "Client"
Cohesion: 0.08
Nodes (3): Client, main(), Starter

### Community 79 - "pathlib"
Cohesion: 0.05
Nodes (8): inspect(), run(), run(), source_inputs(), run(), run(), sha(), rgb()

### Community 80 - "Reference"
Cohesion: 0.10
Nodes (7): Adaptaciones Linux, Evidencia y límites, Integración y perfil del contador, Procedencia y construcción, Resources original sobre Linux, PublicResourcesProbe, Reference

### Community 81 - "Checkpoint y recuperación"
Cohesion: 0.67
Nodes (3): Al cerrar un hito o antes de interrumpir/reiniciar, Al retomar, Checkpoint y recuperación

### Community 82 - "aosp-critical-host/native-probe.cpp"
Cohesion: 0.07
Nodes (20): compare(), context(), floating(), integer(), JNI_OnLoad(), lower(), read(), record() (+12 more)

### Community 83 - "ROADMAP.md"
Cohesion: 0.33
Nodes (3): Historia preservada · no establece requisitos vigentes, Mapa del proyecto con Graphify, Fuente de ingeniería fijada · Android16 QPR2

### Community 84 - "Renderer"
Cohesion: 0.13
Nodes (4): Message, Node, Renderer, Canvas

### Community 85 - "runtime.rs"
Cohesion: 0.06
Nodes (13): Key, Back, Backspace, Character, Down, Enter, Left, Menu (+5 more)

### Community 86 - "Índice de evidencias"
Cohesion: 0.12
Nodes (16): Bootstrap original aislado, Configuración A16 · metadatos host y frontera de seguridad, Configuración nativa A16 · namespaces, classpaths y motor, Entrada original de framework · fallo demostrado, Entrada vigente · contrato Android16, Framework modular y parser original, Fuente completa fijada · A16-QPR2-1, Historia y puertas abiertas (+8 more)

### Community 87 - "Capa de compatibilidad APK propia sobre Linux"
Cohesion: 0.40
Nodes (5): Alcance y recursos, APK propia preparada, Capa de compatibilidad APK propia sobre Linux, Primer estudio implementado, Qué se debe demostrar

### Community 88 - "Capa de compatibilidad APK propia sobre Linux"
Cohesion: 0.03
Nodes (59): Adaptación anterior · cierre del servicio de propiedades, Adaptación anterior · errores de persistencia, Alcance y recursos, Análisis anterior · servicio de propiedades original, APK propia preparada, Arranque actual · LTS con SELinux permisivo, sin política, ART host ejecuta DEX en Linux, Binder original: nuevo resultado parcial (+51 more)

### Community 89 - "APK mínima: contador"
Cohesion: 0.50
Nodes (3): APK mínima: contador, Construcción, Prueba que debe pasar la futura capa

### Community 90 - ".main"
Cohesion: 0.06
Nodes (20): QueueSemanticsProbe, Runnable, Setup, Runnable, Runnable, Setup, Runnable, Runnable (+12 more)

### Community 91 - ".process_input_event"
Cohesion: 0.21
Nodes (6): Shortcut, Exit, Home, Resume, Vt, TvCompositor

### Community 92 - "RuntimeProbe"
Cohesion: 0.39
Nodes (3): Increment, Operation, RuntimeProbe

### Community 94 - "APK original en el compositor propio"
Cohesion: 0.50
Nodes (3): APK original en el compositor propio, Límites y siguiente dirección, Prueba verificada

### Community 95 - "ART host para la capa APK"
Cohesion: 0.33
Nodes (5): ART host para la capa APK, Fuentes y alcance, Investigación modular de la plataforma original, Pruebas separadas, Resultado del primer experimento

### Community 96 - "hashlib"
Cohesion: 0.11
Nodes (10): verify(), sha(), main(), sha(), original(), sha(), sha(), sha() (+2 more)

### Community 97 - "Constructor original de View con recursos del APK"
Cohesion: 0.33
Nodes (5): Constructor original de View con recursos del APK, Frontera final registrada, Fronteras observadas, Log nativo resuelto y siguiente recurso del sistema, Trabajo posterior

### Community 98 - "Activity"
Cohesion: 0.12
Nodes (4): MainActivity, MainActivity, Activity, TextView

### Community 99 - "identity.rs"
Cohesion: 0.23
Nodes (7): current(), Java_android_os_Binder_clearCallingIdentity(), Java_android_os_Binder_flushPendingCommands(), Java_android_os_Binder_getCallingPid(), Java_android_os_Binder_getCallingUid(), Java_android_os_Binder_isDirectlyHandlingTransaction(), Java_android_os_Binder_restoreCallingIdentity()

### Community 100 - "100-apk-session.sh"
Cohesion: 0.50
Nodes (3): LIBSEAT_BACKEND, 100-apk-session.sh script, XDG_RUNTIME_DIR

### Community 102 - "audit-service-profiles.cpp"
Cohesion: 0.22
Nodes (3): main(), string(), tokens()

### Community 104 - "prepare_factory_inputs.py"
Cohesion: 0.14
Nodes (7): digest(), main(), digest(), fields(), manifest(), run(), varint()

### Community 105 - "Port del framework original: primer cierre de compilación"
Cohesion: 0.20
Nodes (9): Context y Application originales, Despacho y semántica originales, Enlace JNI ya probado, Port del framework original: primer cierre de compilación, Recursos nativos originales en Linux, Referencia de compilación, Resources público original, Resultado y siguiente frontera (+1 more)

### Community 107 - "Contrato experimental del runtime APK"
Cohesion: 0.29
Nodes (7): Canal de prueba, Datos y fallos, Evidencia y aceptación, Historia del prototipo A1/A2 · alcance limitado, Integración actual del principal AOSP, Métricas de ventana, Proceso y entradas

### Community 108 - "Primer runtime APK: ART y API mínima"
Cohesion: 0.50
Nodes (3): Construcción y prueba, Límites actuales, Primer runtime APK: ART y API mínima

### Community 109 - "NativeQueueProbe.java"
Cohesion: 0.13
Nodes (4): NativeQueueProbe, MessageQueue.OnFileDescriptorEventListener, Runnable, ResourcesProbe

### Community 111 - "Inicio del port de vistas originales"
Cohesion: 0.40
Nodes (4): Inicialización original y estados de View, Inicio del port de vistas originales, Primer diagnóstico conservado, Siguiente puerta

### Community 112 - "Port selectivo del framework original a Linux"
Cohesion: 0.18
Nodes (10): Base de estudio fijada, Compilación inicial de vistas, Fronteras concretas, Integración en la APK, JNI Linux verificado, Port selectivo del framework original a Linux, Primer conjunto original compilado, Primer despacho original (+2 more)

### Community 113 - "View"
Cohesion: 0.11
Nodes (6): Main, Runnable, Runnable, Runnable, Runnable, UiShutdown

### Community 115 - "clock"
Cohesion: 0.45
Nodes (8): clock(), Java_android_os_SystemClock_currentThreadTimeMicro(), Java_android_os_SystemClock_currentThreadTimeMillis(), Java_android_os_SystemClock_currentTimeMicro(), Java_android_os_SystemClock_elapsedRealtime(), Java_android_os_SystemClock_elapsedRealtimeNanos(), Java_android_os_SystemClock_uptimeMillis(), Java_android_os_SystemClock_uptimeNanos()

### Community 116 - "ContextAction"
Cohesion: 0.33
Nodes (6): ContextAction, Cancel, Favorite, Hide, Left, Right

### Community 118 - "MessageQueue original: enlace JNI Linux en Rust"
Cohesion: 0.40
Nodes (4): Fuentes originales y adaptación, MessageQueue original: enlace JNI Linux en Rust, Pruebas verificadas, Puerta que sigue abierta

### Community 120 - "Contrato vigente de ejecución APK"
Cohesion: 0.40
Nodes (5): Alcance y frontera con Android completo, Contrato anterior BASE-AOSP-1 · histórico, Experimento vertical para decidir base, Requisitos y evidencia de aceptación, Servicios externos y propietarios

### Community 121 - "Métricas de Resources y ventana Wayland"
Cohesion: 0.40
Nodes (4): Evidencia, Métricas de Resources y ventana Wayland, Pendientes, Sincronización de las capturas

### Community 122 - "FocusStack<T>"
Cohesion: 0.30
Nodes (4): FocusStack, FocusStack<T>, home_returns_without_destroying_app_and_close_restores_focus(), repeated_activation_does_not_duplicate_a_window()

### Community 124 - "src/native_process.rs"
Cohesion: 0.11
Nodes (9): check_failure(), NativeFailure, ShutdownRequested, ShutdownRequestTooLong, NativeProcess, Startup, Component, Diagnostic (+1 more)

### Community 125 - "Handler y Looper originales ejecutan mensajes en Linux"
Cohesion: 0.50
Nodes (3): Handler y Looper originales ejecutan mensajes en Linux, Implementación y fronteras, Pruebas y evidencia

### Community 126 - "tests/native_process.rs"
Cohesion: 0.33
Nodes (14): acknowledgment_does_not_hide_failed_exit(), assert_exited(), cooperative_exit_requires_ack_and_actual_exit(), failure_cannot_be_overridden_by_later_startup_ack(), helper(), malformed_failure_payload_cannot_be_a_typed_original_request(), original_shutdown_is_typed_failure_and_actual_exit_is_collected(), oversize_request_is_explicit_failure_never_truncated_success() (+6 more)

### Community 127 - "Backend"
Cohesion: 0.28
Nodes (3): Backend, init(), Result

### Community 128 - "Java_android_os_Binder_getNativeBBinderHolder"
Cohesion: 0.46
Nodes (3): Java_android_os_Binder_getNativeBBinderHolder(), Java_android_os_Binder_getNativeFinalizer(), Java_com_android_internal_os_BinderInternal_getContextObject()

### Community 129 - "desktop.rs"
Cohesion: 0.31
Nodes (9): collect(), data_directories(), discover(), exec_keeps_arguments_and_shell_metacharacters_literal(), executable(), expand_exec(), locale_hidden_and_desktop_sections_are_respected(), parse_entry() (+1 more)

### Community 131 - "La APK usa el Looper principal original de AOSP"
Cohesion: 0.40
Nodes (4): Ensamblado y ejecución, Evidencia, Hilo y cierre, La APK usa el Looper principal original de AOSP

### Community 133 - "Main.java"
Cohesion: 0.09
Nodes (4): HandlerDispatchProbe, Runnable, ResourceBindingCheck, ViewConstructorProbe

### Community 134 - "duration"
Cohesion: 0.18
Nodes (3): main(), dimensions(), main()

### Community 135 - "Port nativo de recursos de AOSP a Linux"
Cohesion: 0.33
Nodes (5): Comprobación y límites, Fuentes y construcción, Integración en el contador, Port nativo de recursos de AOSP a Linux, Puente JNI sobre ART

### Community 136 - "LinuxChildReaper"
Cohesion: 0.17
Nodes (7): LinuxChildReaper, claimed_, fd_, mask_saved_, observer_, old_mask_, registered_

### Community 140 - "Bootstrap de servicios originales sobre Linux"
Cohesion: 0.29
Nodes (6): Bootstrap de servicios originales sobre Linux, Caché original y endpoint local, Contrato IWindowManager íntegro, Frontera siguiente, Registro local verificado (2026-10-30), Reproducción

### Community 143 - "Context y Application originales sobre Linux"
Cohesion: 0.33
Nodes (5): Construcción y pruebas, Context y Application originales sobre Linux, Límite de servicios Linux, Pendientes, Segunda APK independiente

### Community 144 - "Política de animación original y contexto visual"
Cohesion: 0.33
Nodes (5): Frontera gráfica alcanzada, Identidad de display explícita, Política aplicada desde el host real, Política de animación original y contexto visual, Reproducción y evidencias

### Community 146 - "Capability"
Cohesion: 0.15
Nodes (12): Abi, Arm64V8a, ArmeabiV7a, X86, X86_64, Capability, ForceStop, InstallApk (+4 more)

### Community 148 - "extract_platform_modules.py"
Cohesion: 0.29
Nodes (7): digest(), main(), checked_hash(), main(), command(), dump(), entries()

### Community 152 - "archtv-android/src/lib.rs"
Cohesion: 0.16
Nodes (6): command_deadline_and_output_limit_do_not_wait_for_pipe_eof(), drain(), error(), Process, run(), status_requires_exact_boot_value_and_rejects_stale_boot_for_stopped_session()

### Community 153 - "LinuxServiceRegistry"
Cohesion: 0.06
Nodes (7): Endpoint, ServiceCacheProbe, ServiceRegistryChecks, WindowServiceProbe, FileDescriptor, LinuxServiceRegistry, LocalServiceBinder

### Community 154 - "Interpoladores originales HWUI ejecutados en ART"
Cohesion: 0.50
Nodes (3): Alcance pendiente, Interpoladores originales HWUI ejecutados en ART, Prueba ejecutada

### Community 156 - "AndroidProvider"
Cohesion: 0.23
Nodes (7): AndroidProvider, App, AppState, Running, Stopped, Unknown, ProviderResult

### Community 157 - "Log original de AOSP con JNI Linux"
Cohesion: 0.50
Nodes (3): Backend y límites, Comprobación, Log original de AOSP con JNI Linux

### Community 158 - "Recursos de sistema AOSP junto a los del APK"
Cohesion: 0.50
Nodes (3): Construcción y carga explícita, Evidencia y frontera siguiente, Recursos de sistema AOSP junto a los del APK

### Community 159 - "android.rs"
Cohesion: 0.17
Nodes (8): AppId, CONTRACT_VERSION, identity_rejects_commands_and_keeps_android_profiles_distinct(), InstallPolicy, NewOnly, Replace, InstallReceipt, LaunchReceipt

### Community 160 - "dex_inventory"
Cohesion: 0.23
Nodes (9): dex_inventory(), string(), table(), uint(), digest(), decode(), fields(), inventory() (+1 more)

### Community 161 - "Action"
Cohesion: 0.18
Nodes (11): Action, AndroidStart, AndroidStop, Launch, Mute, Quit, Refresh, Resume (+3 more)

### Community 162 - "verify_counter_headless.py"
Cohesion: 0.10
Nodes (6): execute(), kill_group(), ready(), service_check(), start(), wait_for()

### Community 163 - "Consultas IWindowManager respaldadas por Wayland"
Cohesion: 0.33
Nodes (5): Construcción y ejecución, Consultas IWindowManager respaldadas por Wayland, Prueba real, Superficie implementada, Transporte y vida del proveedor

### Community 165 - "ErrorKind"
Cohesion: 0.17
Nodes (12): ErrorKind, BackendFailure, Conflict, IncompatibleAbi, InvalidRequest, NotFound, NotReady, PermissionDenied (+4 more)

### Community 180 - "Port gráfico original: frontera RenderNode"
Cohesion: 0.12
Nodes (13): Construcción nativa, Ejecución y límite actual, RenderNode original ejecutado en ART sobre Linux, Construcción de objetos host, Dependencias identificadas, Evidencia y decisión, Port gráfico original: frontera RenderNode, Próximas comprobaciones necesarias (+5 more)

### Community 196 - "Adaptación tipada de CriticalNative a funciones host HWUI"
Cohesion: 0.50
Nodes (3): Adaptación tipada de CriticalNative a funciones host HWUI, Integración pendiente, Prueba ART

### Community 198 - "Traducción ARM · investigación R6 separada"
Cohesion: 0.50
Nodes (4): Clausura invitada y pruebas antes de elegir, Native Bridge original que reutilizar, Opciones existentes y estado de decisión, Traducción ARM · investigación R6 separada

### Community 199 - "Cliente de accesibilidad original: contratos y frontera Binder"
Cohesion: 0.40
Nodes (4): Cliente de accesibilidad original: contratos y frontera Binder, Contratos AIDL completos, Política de consulta de permisos, Resultado y siguiente implementación

### Community 200 - "ApplicationInfo original y metadatos reales de APK"
Cohesion: 0.40
Nodes (4): ApplicationInfo original y metadatos reales de APK, Constructor View, Lectura y adaptación Linux, Pruebas ejecutadas

### Community 201 - "Contrato vigente · AOSP Android 16 QPR2"
Cohesion: 0.13
Nodes (15): 10. USO DE FUENTES Y REA, 11. VALIDACIÓN, 12. HITOS Y PUERTAS DE DECISIÓN, 13. DOCUMENTACIÓN Y ENTREGA, 1. PROTEGER EL TRABAJO EXISTENTE, 2. BASE AOSP, 3. ARQUITECTURA DE EJECUCIÓN, 4. SIGNIFICADO DE “SIN ANDROID COMPLETO” (+7 more)

### Community 203 - "BootState"
Cohesion: 0.50
Nodes (4): BootState, Completed, Starting, Unknown

### Community 204 - "Page"
Cohesion: 0.18
Nodes (9): Page, Android, Apps, Home, Linux, Menu, Recent, Search (+1 more)

### Community 205 - "AuditedSectionParser"
Cohesion: 0.12
Nodes (14): AuditedSectionParser, active_, current_, kind_, original_, ProfileLine, line, tokens (+6 more)

### Community 206 - "Holder Binder original en ART/Linux"
Cohesion: 0.50
Nodes (3): Construcción, Holder Binder original en ART/Linux, Pruebas y límites

### Community 207 - "Arquitectura vigente · A16-QPR2-1"
Cohesion: 0.04
Nodes (49): Adaptador de directorios proc · verificación offline, Arquitectura vigente · A16-QPR2-1, Artefacto reproducible de política experimental, Base de ingeniería y procedencia, Binder Rust original: regresiones y contrato de identidad, Cierre y comportamiento que hay que conservar, Conjuntos globales: fallo probado de la composición actual, Contraste nativo de transacciones con contexto de seguridad (+41 more)

### Community 213 - ".initialize"
Cohesion: 0.12
Nodes (4): OriginalBootstrapProbe, MetadataProbe, LocalContextProbe, HostProfile

### Community 214 - "Log original con excepciones y líneas largas"
Cohesion: 0.50
Nodes (3): Avance del layout, Log original con excepciones y líneas largas, Pruebas

### Community 216 - "Matriz de aplicaciones reales"
Cohesion: 0.50
Nodes (4): Dependencias y selección de base BASE-AOSP-1, Estado vigente A16-QPR2-1, Inventario de artefactos y evidencia previa, Matriz de aplicaciones reales

### Community 218 - "Roadmap A · plataforma APK general sobre Linux"
Cohesion: 0.20
Nodes (10): Control experimental de namespaces de política, Decisiones offline con herramientas originales, Diagnóstico previo de PropertyInit · superado por el perfil fuente, Historia · etapas anteriores, no prioridad vigente, Integración de política · namespace Linux y conflicto de SID, Perfil de propiedades y diagnóstico previo de opciones, Prioridad vigente · A16-QPR2-1, Puerta vigente: Binder privado y política del Linux anfitrión (+2 more)

### Community 219 - "check_host_security.py"
Cohesion: 0.23
Nodes (6): inspect(), main(), read_status(), read_text(), status_snapshot(), zero_size_selinux_status()

### Community 223 - "SessionState"
Cohesion: 0.33
Nodes (6): SessionState, Running, Starting, Stopped, Suspended, Unknown

## Knowledge Gaps
- **129 isolated node(s):** `archtv-aosp-linux`, `archtv-apk-host`, `archtv-compositor`, `Home`, `Resume` (+124 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1071 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **101 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LinuxWindowService` connect `LinuxWindowService` to `IBinder`, `.state`, `LinuxServiceRegistry`, `.addShellRoot`, `Rect`, `.verifyDisplayHash`, `.overridePendingAppTransitionMultiThumbFuture`, `.registerCrossWindowBlurEnabledListener`, `.registerDisplayFoldListener`, `.registerDisplayWindowListener`, `.addKeyguardLockedStateListener`, `.getWindowInsets`, `.removeRotationWatcher`, `.registerSystemGestureExclusionListener`, `.registerTaskFpsCallback`, `.registerWallpaperVisibilityListener`, `.openSession`, `.screenshotWallpaper`, `.getPossibleDisplayInfo`, `.requestAssistScreenshot`, `.setDisplayWindowInsetsController`, `.setDisplayWindowRotationController`, `.dismissKeyguard`, `.updateDisplayWindowRequestedVisibilities`, `.exitKeyguardSecurely`, `.registerPinnedTaskListener`, `.requestAppKeyboardShortcuts`, `.registerShortcutKey`, `.getCurrentImeTouchRegion`, `.overridePendingAppTransitionRemote`, `.setTaskTransitionSpec`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **What connects `archtv-aosp-linux`, `archtv-apk-host`, `archtv-compositor` to the rest of the system?**
  _129 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `worker.rs` be split into smaller, more focused modules?**
  _Cohesion score 0.0953058321479374 - nodes in this community are weakly interconnected._
- **Why does `TvCompositor` connect `TvCompositor` to `xdg_shell.rs`, `duration`, `mod.rs`, `input.rs`, `drm.rs`, `session.rs`, `.process_input_event`, `Backend`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Should `resources-jni.cpp` be split into smaller, more focused modules?**
  _Cohesion score 0.12145390070921985 - nodes in this community are weakly interconnected._
- **Why does `WindowPolicyState` connect `.state` to `WindowPolicyState.java`, `LinuxWindowService`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Should `Client` be split into smaller, more focused modules?**
  _Cohesion score 0.07553143374038897 - nodes in this community are weakly interconnected._