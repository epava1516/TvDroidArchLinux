# Mapa del proyecto con Graphify

Graphify oficial (`graphifyy` en PyPI), versión 0.9.97. Se instala aislado en
`~/.local/share/archtv-tools/graphify`, con ejecutable en `~/.local/bin/graphify`.
La instalación local y las dependencias están fijadas en lab/graphify/.

```bash
./scripts/68-graphify.sh --apply
./scripts/graphify.sh build
./scripts/graphify.sh status
./scripts/graphify.sh query 'TvCompositor focus shell supervisor'
./scripts/graphify.sh explain 'TvCompositor'
./scripts/graphify.sh update
```

Las vistas generadas se abren sin servidor:

- [Grafo interactivo](../graphify-out/graph.html).
- [Árbol de archivos y símbolos](../graphify-out/GRAPH_TREE.html).
- [Informe de arquitectura](../graphify-out/GRAPH_REPORT.md).

La integración Codex está en `.codex/skills/graphify/`, con instrucciones de
consulta en AGENTS.md. Estará disponible cuando Codex cargue de nuevo las skills
del proyecto. El instalador registra hooks Git para reconstruir después de
commits y cambios de rama. Los hooks no viajan con Git: ejecutar el instalador
en cada clon. La configuración del proyecto, la skill y el grafo sí se versionan.

El mapa usa extracción AST local y dependencias Cargo, con un worker y sin backend
LLM. Reports, cachés y código del laboratorio upstream quedan excluidos. Las
relaciones extraídas e inferidas conservan las etiquetas que genera Graphify.
No se ha activado Graphify Cloud ni un proveedor externo.

El grafo muestra estructura y relaciones del código. **ROADMAP.md y las pruebas
son la fuente del avance real:** el número de nodos no acredita que una función
esté terminada. La documentación no está indexada semánticamente en esta
configuración. `status` combina los conteos del mapa con los hitos del roadmap.

Fuente: [repositorio oficial de Graphify](https://github.com/Graphify-Labs/graphify).
