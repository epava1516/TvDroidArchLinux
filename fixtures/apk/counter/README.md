# APK mínima: contador

org.archtv.probe es una APK Android Java propia para el primer experimento de
compatibilidad. Usa una Activity, LinearLayout, TextView, Button, un listener y
SharedPreferences. No incluye JNI, Kotlin, AndroidX ni bibliotecas adicionales.
No exige pantalla táctil; el botón pide foco para la prueba con teclado/mando.

## Construcción

Instalar manifests/apk-lab.txt y usar un directorio de herramientas de laboratorio:

```bash
python tools/apk/fetch_fixture_tools.py "$HOME/.cache/archtv/apk-build-tools"
python tools/apk/build_fixture.py --tools "$HOME/.cache/archtv/apk-build-tools" --output dist/apk/counter-nueva-prueba
```

El destino debe ser nuevo. toolchain.json fija URLs y SHA-256 de AAPT2, D8/R8 y
android.jar API 28 obtenido de una revisión AOSP. Java 17 compila a bytecode Java 8;
D8 produce DEX con mínimo API 21. El manifiesto declara target API 28: no prueba
compatibilidad con todas las APIs actuales. Las clases de referencia se usan al
compilar y no se incluyen como framework dentro de la APK.

El script genera APK sin firmar, APK con firma JAR v1 de prueba, badging,
inventario y procedencia con hashes. La clave local de prueba se guarda en la
caché de herramientas, fuera de Git; la contraseña archtv-fixture es exclusiva de
ese material de laboratorio. El certificado público sí forma parte de la APK.
No se afirma validación APK v2/v3 ni identidad de producción. La firma y sus fechas
no forman parte de la comprobación de repetibilidad de la APK sin firmar.

golden/counter.apk conserva la primera fixture firmada del experimento. Sus
fuentes e informe están en reports/a0-fixture/. Dos construcciones sin firmar
resultaron iguales byte por byte con este entorno. No es una prueba de ejecución.

## Prueba que debe pasar la futura capa

1. Abrir esta APK sin traducir sus fuentes a una aplicación Linux distinta.
2. Ejecutar el DEX de MainActivity y mostrar el texto y el botón en Wayland.
3. Recibir eventos reales: cada activación incrementa exactamente una vez.
4. Conservar el contador después de cerrar y volver a abrir el proceso.
5. Cerrar y liberar ventana/recursos; repetir sin procesos huérfanos o crecimiento
   de memoria no explicado, y medir respuesta y consumo.

El inventario muestra un DEX de unos 3 KiB, tres clases propias, 17 descriptores
externos de plataforma y cero bibliotecas nativas. No equivale a 17 APIs suficientes:
la herencia, resolución de métodos y dependencias del runtime requieren análisis.
Getters como getString/getSharedPreferences pueden referirse al propietario de la
app en DEX y necesitan resolución hacia la superclase; el analizador estático
actual no resuelve esa herencia. El inventario también contiene anotaciones.

Esta APK ya ejecuta su DEX en ART host con el subconjunto de runtime/apk:
onCreate, listener, textos de resources.arsc y contador persistente entre procesos.
El runtime no contiene clases de la app. Ver reports/a1-counter-headless/ y
tools/apk/verify_counter_headless.py. También pasan ventana/entrada Wayland y la
integración del principal AOSP: docs/APK-LOOPER-AOSP.md, reports/aosp-ui-headless/
y reports/aosp-main-ui-wayland/. No acredita compatibilidad general ni estabilidad prolongada.
