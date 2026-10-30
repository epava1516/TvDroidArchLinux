# Holder Binder original en ART/Linux

El constructor original de Binder ya asigna su holder nativo en Linux.
runtime/aosp/native/binder-holder-jni.cpp incluye android_util_Binder.cpp original
y publica dos entradas JNI con nombre: getNativeBBinderHolder y
getNativeFinalizer. Sus cuerpos llaman las funciones AOSP sin modificar.

La primera crea JavaBBinderHolder con new; el finalizador devuelve Binder_destroy,
que destruye ese objeto. Se conservan Mutex, wp<JavaBBinder> y sp<IBinder> del
holder original. No se devuelve un identificador ficticio ni se reemplaza su
estado por una estructura propia. El constructor Java original conserva su
registro en NativeAllocationRegistry.

## Construcción

binder-sources.json fija Binder, binderthreadstate y core/jni de las revisiones
Android 13 ya utilizadas, más libhwbinder 6a99431c775b748ef15c205d8fd0dfb44a6e0389.
Se verifican todos los archivos de esos subárboles, las dependencias androidfw y
las cabeceras nativehelper. La compilación prioriza las cabeceras Binder propias
y exporta únicamente stdatomic.h original de Bionic para compatibilidad C++ con
libc++ de ART; no añade el árbol Bionic completo a los includes glibc.

build_binder_holder.py usa secciones por función/dato, visibilidad oculta y un
mapa de exports para conservar solamente las dos entradas. Enlaza sin símbolos
sin resolver contra los archivos host originales ya verificados. Comprueba con
nm los dos símbolos exportados; conserva comandos, compilador, hashes de
manifiestos, fuentes propias/JNI/atomic, archivos estáticos, libc++ y biblioteca.
El código JNI completo se analiza al compilar, pero sus rutas de transporte no
se enlazan a este perfil ni se ejecutan.

```bash
python tools/apk/fetch_androidfw_sources.py "$HOME/.cache/archtv/binder-port" --manifest runtime/aosp/binder-sources.json
python tools/apk/build_binder_holder.py --sources "$HOME/.cache/archtv/binder-port" --androidfw-sources "$HOME/.cache/archtv/androidfw-port" --androidfw-build dist/apk/androidfw-clang-1 --hwui-sources "$HOME/.cache/archtv/hwui-port" --art "$HOME/.cache/archtv/art-host/host/art-13.0.0" --output dist/apk/binder-holder-nuevo
python tools/apk/verify_binder_holder.py --build dist/apk/binder-holder-nuevo --output dist/apk/binder-holder-prueba-nueva
```

## Pruebas y límites

La prueba nativa carga la biblioteca de producción y llama las entradas originales
con contexto JNI nulo, que estas funciones no utilizan. Crea 128 holders vivos
con direcciones distintas, libera todos mediante el finalizador original y
repite 100 ciclos: 12.800 asignaciones/liberaciones. El ejecutable de prueba usa
AddressSanitizer y LeakSanitizer; la biblioteca de producción no está compilada
con instrumentación, por lo que no se afirma cobertura de todos sus accesos.
LeakSanitizer necesita ejecutarse fuera del sandbox que impide ptrace; no se
modifica ninguna opción del kernel. La ejecución exterior termina sin errores
ni fugas detectadas. El primer fallo del sandbox se conserva como tal.

En ART -Xint -Xcheck:jni se construyen 32 Binder originales con holders únicos,
se asocian interfaces locales y se comprueba identidad, rechazo de descriptor
incorrecto y estado de tokens locales. getExtension sigue produciendo
UnsatisfiedLinkError esperado: no se acredita extensión ni transporte. Esta
prueba no observa la ejecución del finalizador por GC de ART; la liberación se
prueba por separado en el ejecutable nativo.

verify_wayland_resize.py admite --window-binder-holder-build, valida el hash de
la biblioteca y exige BINDER_HOLDER_ART_OK. Conserva medida en cinco casos,
consulta de permisos, resize 960×540→800×450, animación y muerte/cierre del
proveedor. El layout supera la construcción del cliente AIDL de accesibilidad,
pero ahora se detiene en LineBreakBufferedWriter ausente al registrar el fallback
de recursos de foco. view_layout_pass continúa siendo false.

Los registros y resultados están en reports/aosp-binder-holder. No hay todavía
layout completo, dibujo original, soporte de accesibilidad ni IPC Binder entre
procesos; A3–A5 permanecen abiertos.
