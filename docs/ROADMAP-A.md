# Roadmap A · compatibilidad APK mínima sobre Linux

Objetivo aclarado por el usuario: estudiar AOSP y reproducir o reutilizar el mínimo
necesario para ejecutar APK de forma estable sobre Linux, dentro de nuestra sesión
Rust/Smithay. No se persigue arrancar un sistema Android completo ni envolver
Waydroid. El éxito se mide por ejecución real de aplicaciones, no por boot Android.

| Etapa | Trabajo concreto | Puerta de salida | Estado |
| --- | --- | --- | --- |
| A0 · superficie real | APK propia pequeña, inventario DEX/recursos/JNI y pruebas funcionales; revisar contrato según esas necesidades | APK y fuentes fijadas, APIs realmente usadas identificadas, pruebas reproducibles | En curso: analizador y APK propia compilada con hashes; ejecución pendiente |
| A1 · ejecución DEX | Estudiar ART/libcore en modo host y alternativas; prototipo de ejecución sobre Linux sin sistema Android | Código DEX de la APK ejecutado con salida verificable, sin Waydroid ni arranque Android | Pendiente |
| A2 · primera interfaz | Subconjunto medido de Activity, ciclo de vida, recursos, View/texto/botón y entrada; puente hacia Wayland/Rust | APK propia sin modificar abre ventana, responde a entrada, guarda estado y se cierra correctamente | Pendiente |
| A3 · servicios mínimos | JNI/ABI/Bionic donde sean necesarios, gráficos, audio, red, archivos y permisos según APK de prueba | Pruebas por API/servicio, errores explícitos en funciones ausentes y recuperación | Pendiente |
| A4 · compatibilidad y estabilidad | APK reales por ABI/API, reflexión, WebView y demás dependencias descubiertas; ampliar la capa con evidencia | Matriz por aplicación, pruebas prolongadas, reinicios y mediciones; fallos y cobertura registrados | Pendiente |
| A5 · distribución | Runtime y servicio anfitrión propios, paquetes, actualizaciones, migración de datos e integración TV | Instalación limpia sin Waydroid ni sistema Android completo, apps verificadas, actualización y rollback | Pendiente |

## Próximo experimento

1. Crear una APK propia con una Activity, texto, botón y contador persistente,
   sin bibliotecas JNI ni dependencias adicionales en su primera versión.
2. Fijar sus fuentes, SDK, APK y hashes; analizar referencias y recursos.
3. Probar ejecución DEX fuera de Android. Evaluar reutilización selectiva de ART
   y libcore antes de escribir un runtime completo desde cero.
4. Implementar las APIs que esa APK requiere y un puente de ventana/entrada hacia
   el compositor; ninguna pantalla simulada cuenta como ejecución de la APK.
5. Verificar cierre, estado, repetición y consumo. Ampliar el conjunto de APK y
   APIs con resultados de ejecución, manteniendo la meta de estabilidad.

AOSP aporta especificaciones y componentes que se estudiarán individualmente.
Zygote, system_server, SystemUI, SurfaceFlinger, HAL y Binder no se convierten en
requisitos globales por defecto: cada dependencia deberá justificarse o adaptarse
según la ruta elegida y las aplicaciones. Tampoco se afirma que todos puedan
eliminarse conservando cualquier API; esa compatibilidad debe demostrarse.

## Corrección del enfoque anterior

Los tipos AndroidProvider y el adaptador de estado Waydroid publicados son trabajo
previo y una referencia del laboratorio. No son el entregable de este roadmap ni
un prerrequisito para A1. Se detuvo su ampliación; el inventario Waydroid no
publicado se archivó fuera del repositorio. El contrato mínimo se revisará a la
luz de los experimentos, sin exigir sys.boot_completed ni un arranque AOSP.

Las validaciones funcionales, de ligereza, estabilidad e instalación del proyecto
siguen vigentes. H6 contiene resultados del laboratorio Waydroid; no se reutilizan
como prueba de la futura capa. La infraestructura para compilar una plataforma
AOSP completa no se presupone necesaria para investigar este runtime mínimo.

## Fixture disponible

fixtures/apk/counter contiene fuentes, recursos, manifiesto y APK de prueba
propia. Compila con AAPT2/D8 y clases API 28 fijadas por hash, sin arrancar Android.
Dos builds sin firma resultaron idénticos en esta VM; firma JAR v1 de laboratorio
comprobada. Inventario: un DEX, 17 referencias de tipo externas y sin JNI.
Ver su README y reports/a0-fixture/. La siguiente puerta es ejecutar ese DEX
y resolver sus APIs fuera de Android, antes de afirmar compatibilidad de interfaz.
