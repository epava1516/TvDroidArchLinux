Verificación criptográfica de Markor intacta con el módulo host apksig original, revisión fijada por manifest.lock.xml. Android.bp excluye los plugins KMS AWS/GCP: core-build.json reproduce esa composición sin editar fuentes. build.json conserva el primer fallo al compilar también los plugins sin sus SDK externos.

verification.json contiene positivo API36 y negativo sobre copia alterada de classes.dex; el original conserva SHA256 c105bf5cc9530f7486b984323a185c17086b459a56ec936a5990ceb8da3d8440. Firma v2 válida, certificado SHA256 57d106d0cfa8763442b3645ef2741c38bb820bd56fd4612bf40a23b6d998be5e. No se ha establecido confianza externa en la identidad del productor.

REA MCP ev_71453fb05eb5c390b71096fbf3e41ec8da4dda7f0466b54da17dfda79c2f5114 sólo inspeccionó declaraciones; la verificación real la ejecutó apksig en Linux/JVM. No ejecución Android, instalación PackageManager ni aceptación de recorrido.
