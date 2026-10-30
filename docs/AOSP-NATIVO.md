# Dirección futura: entorno APK propio sobre Linux

Propuesta registrada el 30 de octubre de 2026 a petición del usuario. El objetivo
es sustituir la dependencia operativa de Waydroid por un entorno Android propio,
basado en AOSP, integrado con el compositor Rust/Smithay y la distribución Arch TV.
Es una evolución posterior al roadmap H0–H9; no está implementada ni validada.

## Qué significa ejecutar APK de forma nativa

Los procesos compartirían el kernel Linux del equipo, sin emular una máquina
Android completa para una ABI coincidente. Un APK sigue necesitando las APIs
Android, el runtime ART para DEX, bibliotecas nativas compatibles con Bionic y
servicios de plataforma. ART por sí solo no ejecuta cualquier aplicación Android.
Una biblioteca ARM dentro del APK tampoco se convierte automáticamente a x86_64.

AOSP proporciona el código de la plataforma, no una biblioteca lista para enlazar
con glibc y ejecutar cualquier APK de escritorio. Véanse la
[arquitectura oficial](https://source.android.com/docs/core/architecture) y
[ART](https://source.android.com/docs/core/runtime).

## Arquitectura que se investigará

- Shell/compositor propios en Rust: navegación TV, ciclo de vida de ventanas,
  foco, entrada y presentación Wayland.
- Servicio anfitrión propio en Rust: instalación, inventario, lanzamiento,
  detención y estado de apps mediante un contrato independiente del backend.
- Userspace AOSP controlado: ART, Zygote, servicios de paquetes/actividades,
  recursos, permisos, Binder y bibliotecas Android que requieran las apps.
- Integraciones de gráficos, audio, entrada, red, almacenamiento y energía.
  Primera ruta gráfica: conservar SurfaceFlinger y adaptar su salida a Wayland;
  después medir si una integración más directa reduce coste sin romper APIs.
- Separación de datos y privilegios de apps. Compartir kernel no exige compartir
  el espacio de nombres ni conceder acceso general al sistema anfitrión.

Esta es una hipótesis de diseño que debe probarse. El backend Rust de AIDL
[está documentado por AOSP](https://source.android.com/docs/core/architecture/aidl/aidl-backends),
pero depende del runtime Binder de Android: no implica que todo AOSP sea Rust ni
que funcione directamente contra las bibliotecas glibc del anfitrión.
Las [HAL](https://source.android.com/docs/core/architecture/hal) identifican los
contratos de hardware a adaptar. Se reutilizarán componentes AOSP mantenidos;
la lógica anfitriona nueva se desarrollará preferentemente en Rust.

## Etapas y pruebas de salida

| Etapa | Entregable | Evidencia necesaria |
| --- | --- | --- |
| A0: contrato | Protocolo de apps independiente del proveedor, con adaptador Waydroid inicial | Mismas pruebas de instalar/listar/lanzar/parar/estado y errores; shell sin comandos específicos del proveedor |
| A1: build AOSP | Manifest fijado a revisiones, producto x86_64, parches y licencias | Build reproducible en infraestructura adecuada; hashes e inventario; arranque completo sin paquetes ni servicios Waydroid |
| A2: primera APK | Userspace mínimo, Binder y ciclo de vida de apps | APK propia Java/Kotlin instalada, ventana e interacción sobre nuestro compositor, sys.boot_completed=1, cierre y reinicio |
| A3: integración | Gráficos, mando/IME, audio/vídeo, red y archivos | Matriz de pruebas funcionales, formatos/sincronización de buffers, permisos y recuperación ante fallos |
| A4: compatibilidad | Conjunto de APK reales con ABIs y APIs declaradas | Resultados por app y arquitectura, JNI/Bionic, WebView y servicios requeridos; pruebas CTS aplicables sin afirmar certificación |
| A5: distribución | Paquetes/imagen propios, actualizaciones y datos migrables | Instalación limpia sin Waydroid, actualización/rollback, conservación de datos y métricas comparables con H6/H7 |

La retirada de Waydroid ocurrirá cuando el entorno propio pase las mismas pruebas
con mejor control de mantenimiento e integración. Hasta entonces es un backend
de referencia que permite avanzar y detectar requisitos reales de las APK.
La compatibilidad con Google Play Services, certificaciones y DRM comercial se
estudiará por separado; no se deduce de disponer del código AOSP.

## Recursos y decisiones pendientes

La [guía de compilación actual](https://source.android.com/docs/setup/start/requirements)
indica 400 GB libres y 64 GB de RAM para la estación de desarrollo. La VM actual
de unos 1,9 GiB sirve para ensayos limitados de ejecución, no satisface ese perfil
de compilación. Se elegirá infraestructura de build antes de descargar AOSP.

Quedan por fijar la versión soportada, ABI inicial, perfil de seguridad, conjunto
de servicios mínimo y estrategia de HAL/gráficos. La memoria y la CPU deben
medirse tanto en reposo como con aplicaciones; quitar el nombre Waydroid no
prueba por sí mismo una reducción de consumo.
