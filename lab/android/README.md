# Laboratorio Android H6

La aplicación de prueba es VLC 3.7.1 x86_64, descargada del servidor oficial de
VideoLAN y contrastada con el SHA-256 publicado. El APK permanece en la caché
local ~/.cache/archtv/apk/; este directorio versiona URL y checksum, no el APK.

Scripts internos 90/91 requieren una sesión PAM/logind y se invocan con la prueba
92, ejecutada como usuario con sudo disponible. La prueba 92 arranca una sesión
DRM temporal, espera sys.boot_completed=1, recoge logs y captura y restaura VT.
El resultado PARTIAL no certifica aplicaciones, audio/vídeo ni toda la integración.

```bash
CARGO_TARGET_DIR="$HOME/.cache/archtv/smithay/target" ./scripts/92-android-boot-probe.sh --apply
```

La sesión interna 93 combina shell y compositor para probar inicio Android desde
ajustes, búsqueda/lanzamiento de VLC, Inicio y reanudación. android-ui-probe.py
inyecta un teclado uinput real; sus modos son start, vlc, home, resume y android.
No es un sustituto de pruebas con mando físico. La instalación del APK y su
primera configuración son pasos de laboratorio separados.

FFmpeg (manifests/android-test-lab.txt) genera el clip original de color y tono;
no es una dependencia del shell. VLC necesita completar su tutorial de vídeo:
una imagen visible con el tutorial y un audio silencioso no prueban reproducción.
El monitor PipeWire permite medir el trayecto digital de audio; no demuestra
sonido acústico o compatibilidad HDMI en hardware físico.

La prueba experimental 94 presupone una sesión 93 con VLC activo y su tutorial
configurado. Sirve el clip únicamente en 192.168.240.1:8765 y captura el monitor
del sink. La selección por intent y la orden de reproducción usan comandos
Android de preparación; no son prueba de mando a través del compositor. Ese
recorrido se verifica por separado con android-ui-probe.py.

```bash
ARCHTV_ANDROID_REPORT="$PWD/reports/h6-media" ./scripts/94-android-media-probe.sh --apply
```

El script solo informa CAPTURED. Para validar reproducción deben avanzar los
frames del contenido (no basta un cambio del overlay) y mantenerse el tono de
440 Hz durante la captura. En el primer ensayo no se cumplieron estas condiciones.

## Perfil VLC de laboratorio

vlc-tv-software-profile.json registra las preferencias y fuentes oficiales fijadas a VLC 3.7.1.
El helper scripts/lib/vlc-test-profile.py requiere el contenedor detenido y un
directorio de informe nuevo; conserva las preferencias anteriores y sus UID y
permisos al reemplazarlas. Solo configura la APK de prueba, no el sistema Android.

verify-android-media.py usa el venv de análisis visual. Rechaza vídeo sin cambios
y exige al menos 3 s consecutivos de tono con ventanas de 100 ms y actividad
suficiente; hay que inspeccionar las capturas para descartar cambios de overlays.
El campo pass no acredita estabilidad, HDMI ni compatibilidad física.

Las capturas de audio se conservan en FLAC sin pérdida. Para repetir el análisis
tras clonar el repositorio, decodificar audio-monitor.flac a audio-monitor.wav
con FFmpeg antes de ejecutar verify-android-media.py. Se guarda el SHA-256 de
los PCM decodificados; el contenedor WAV original puede tener otra cabecera.

Resultados estrictos guardados (ventanas de audio de 100 ms):

| Ensayo | Vídeo cambia | Mayor tramo de tono detectado | Resultado conjunto |
| --- | --- | --- | --- |
| VLC TV/software | Sí | 0,0 s | Incompleto |
| VLC salida alternativa | Sí | 0,6 s | Incompleto |
| Reproductor AOSP | No | 2,5 s | Incompleto |

Los volúmenes de la fuente difieren entre los dos ensayos VLC, por lo que no se
puede atribuir la diferencia solo al backend. Los PNG muestran además un ANR de
System UI. El incidente posterior afectó toda la VM; está documentado por separado
en docs/INCIDENTE-VM-20261030.md. La aplicación del helper con Android detenido
conservó UID/GID 10125 y permisos 0660, y retiró el backend experimental aout.
