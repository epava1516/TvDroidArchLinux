# Roadmap A · proveedor Android propio basado en AOSP

El usuario pidió avanzar A0 en paralelo a H0–H9. Se mantiene todo el alcance de
ambos: A no sustituye las pruebas multimedia, estabilidad, empaquetado e instalación
pendientes. El objetivo final es ejecutar apps Android con userspace AOSP propio,
compartiendo kernel Linux y usando nuestra sesión Rust/Smithay, sin Waydroid.

| Etapa | Trabajo concreto | Puerta de salida | Estado |
| --- | --- | --- | --- |
| A0 · contrato | Tipos Rust, adaptador Waydroid, catálogo y acciones del shell a través del proveedor, errores y plazos | APK real instalada, listada, lanzada y parada; boot y errores comprobados; shell sin comandos Waydroid | En curso: tipos, contrato y consulta de estado Waydroid conectada al shell; resto del adaptador pendiente |
| A1 · plataforma | Elegir versión/API, fijar manifests y toolchain, producto x86_64, inventario/licencias, infraestructura de build | Build registrado y repetible; arranque completo sin servicios ni paquetes Waydroid | Pendiente |
| A2 · primera APK | Binder, Bionic, ART/Zygote, servicios mínimos de paquetes/actividades y recursos; APK propia | Instalación, ventana Wayland, entrada, cierre y reinicio de APK propia; boot confirmado | Pendiente |
| A3 · integración TV | SurfaceFlinger/HAL hacia Wayland, mando/IME, audio/vídeo, red, archivos, energía y aislamiento | Matriz funcional con formatos/sincronización y recuperación; controles de permisos | Pendiente |
| A4 · compatibilidad | Apps reales por ABI/API, JNI, WebView y servicios requeridos; pruebas CTS aplicables | Matriz con resultados y límites; ninguna afirmación de certificación sin evidencia | Pendiente |
| A5 · producto | Paquetes propios, imagen, actualizaciones, rollback y migración de datos desde el proveedor anterior | Instalación nueva sin Waydroid, apps verificadas, recuperación y métricas comparables | Pendiente |

## Orden inmediato A0

1. Definir contrato y tipos independientes en archtv-core, con errores y plazos.
2. Añadir adaptador Waydroid con límites de procesos/salida y pruebas de errores.
3. Consumirlo desde los workers del shell; retirar comandos específicos de la UI.
4. Migrar inventario y lanzamiento Android conservando favoritos y aplicaciones Linux.
5. Probar APK real y fallos en una plataforma estable; registrar qué queda sin verificar.
6. Congelar v1 solo tras esa integración. Después definir IPC y servicio anfitrión.

La etapa 1 tiene una primera implementación en android.rs. Las etapas 2/3
comenzaron con status en archtv-android y su consumo desde el worker de estado.
El contrato se detalla en CONTRATO-ANDROID.md. No constituye un proveedor AOSP operativo. Las pruebas de
identidad/boot son unitarias; el resto requiere adaptador y evidencia de ejecución.

## Decisiones que debe resolver A1

- Versión AOSP y nivel de API, revisión exacta y calendario de mantenimiento.
- ABI x86_64 inicial y declaración explícita de ABIs adicionales.
- Mínimo de servicios y HAL requerido por la APK propia, no por suposición.
- Infraestructura de compilación y almacenamiento; no descargar AOSP en esta VM
  sin resolver esos recursos y su capacidad de mantenimiento.
- Límites de privilegios, perfiles, datos y asociación autenticada de ventanas.

Las puertas H6/H7 siguen determinando si la plataforma anfitriona puede usarse
para validar multimedia y rendimiento. Los soft lockups actuales de la VM se
registran por separado; no se atribuyen al futuro proveedor AOSP.
