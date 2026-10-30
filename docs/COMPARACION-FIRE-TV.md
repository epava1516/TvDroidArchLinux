# Comparación de composición con Fire TV 2026

Se utiliza la fotografía principal publicada por Amazon, enlazada en
[las referencias](REFERENCIAS-FIRE-TV.md). El fichero se conserva en la caché
local de análisis, fuera del producto y del repositorio. Su SHA-256 y URL exacta
quedan registrados en reports/h5-layout/layout-metrics.json.

La fotografía de 1600×900 incluye el marco del televisor. Se recorta el área
x=164, y=80, ancho=1272, alto=715 y se normaliza a 1920×1080. La lectura manual
tiene una incertidumbre de ±3 píxeles originales, aproximadamente ±4,5 píxeles
normalizados; no proporciona una especificación oficial de Amazon.

| Elemento | Referencia normalizada: x, y, ancho, alto | Arch TV: x, y, ancho, alto |
| --- | --- | --- |
| Inicio seleccionado | 277,7; 43,8; 64,9; 66,5 | 277; 43; 66; 66 |
| Botón principal | 102,6; 487,9; 208,3; 65,0 | 104; 488; 210; 64 |
| Primera tarjeta | 102,6; 607,2; 323,0; 182,8 | 104; 608; 324; 184 |
| Primera app compacta | 102,6; 815,7; 149,4; 83,1 | 104; 816; 150; 84 |
| Panel inferior | 102,6; 921,4; 1711,7; 135,9 | 104; 922; 1712; 135 |

Las posiciones y dimensiones objetivo quedan dentro de la incertidumbre de la
lectura. La detección independiente del botón blanco en las capturas obtiene
103,488,207,63 en la referencia y 104,488,210,64 en el shell. Los contornos naranja
y cian de layout-overlay.png se dibujan exclusivamente sobre nuestra captura;
no redistribuyen píxeles de la fotografía de Amazon.

Esto acredita proporciones de la pantalla Inicio, no igualdad píxel a píxel ni
identidad de todas las pantallas. La tipografía, etiquetas, catálogo, arte y
semántica son propios. Los iconos Linux/Android y recientes llevan a funciones
reales. El foco añade un borde visible; la navegación con uinput y persistencia
están registradas en reports/h5-interactive/. Falta validar el mando físico en H7.

El fondo original fue generado con la herramienta integrada imagegen. El prompt
y procedencia están en crates/archtv-shell/assets/. Se carga fuera del hilo de
interacción; su coste total de sesión se medirá en H7.

Para reproducir el análisis con la referencia descargada en la caché:

```bash
python -m venv ~/.local/share/archtv-tools/visual-analysis
~/.local/share/archtv-tools/visual-analysis/bin/pip install -r lab/visual/requirements.txt
~/.local/share/archtv-tools/visual-analysis/bin/python scripts/lib/layout-reference.py \
  ~/.cache/archtv/references/fire-tv-2026-home.jpg \
  reports/h5-interactive/states/home.png reports/h5-layout
```
