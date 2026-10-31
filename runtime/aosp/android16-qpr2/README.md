# Fuente de ingeniería fijada · Android16 QPR2

`release.json` identifica la referencia vigente; `source-manifest.xml` conserva
el manifiesto oficial sin modificar y `manifest.lock.xml` fija los 1.013 checkout
paths a commits. `manifest.lock.json` conserva ref, objeto tag, commit peeled,
URL y SHA-256 de cada respuesta Gitiles. No contiene fuentes sincronizadas,
SDK, binarios, imagen instalable ni validación de runtime.

El derivado hace absoluto el remote AOSP, conserva atributos/copyfiles/linkfiles
de proyectos y omite la optimización opcional superproject. El tag consultado
no fue anunciado para ese superproject; no se lo sustituye por una rama flotante.
Formato/comentarios del XML derivado no se conservan; el original permanece íntegro.

Reproducción desde la caché de metadatos del laboratorio, sin red ni descargar AOSP:

```sh
python tools/aosp/lock_release_manifest.py \
  --manifest runtime/aosp/android16-qpr2/source-manifest.xml \
  --expected-sha256 19db4af44aa74ea4ed07bf602f5805476bab1c821d59ba818031022280ae055f \
  --tag android-16.0.0_r4 --cache "$HOME/.cache/archtv/aosp16-qpr2/refs" \
  --offline --output dist/aosp16/source-lock-nuevo
```

El output debe ser nuevo. Sin `--offline` sólo consulta las refs faltantes en
Gitiles oficial, con hasta cuatro workers. No resuelve topologías arbitrarias:
requiere este tipo de manifest con tag uniforme anotado y proyectos únicos;
referencias incompletas no producen XML aprobado. Para otra release hay que
verificar primero su manifiesto/identidad y registrar su SHA-256, no actualizar
el tag por su número ni prometer seguridad vigente por reproducibilidad.

Los tests de reproducción, inputs rechazados y objetos principales contrastados
se guardan en reports/android16-source-lock/. La GSI oficial x86_64 de build coincidente ya está verificada y sus componentes
originales se han extraído sin montar ni arrancar la imagen. La trazabilidad
binaria está en `release.json` y reports/android16-native-base/. `linker --help`,
`--list dalvikvm64` y `dalvikvm64 -help` pasan en un harness aislado con rutas
aplanadas; configuración original, DEX, APK, seguridad y licencias siguen pendientes;
ver [contrato](../../../docs/CONTRATO-APK.md) y [estado](../../../docs/ESTADO.md).
