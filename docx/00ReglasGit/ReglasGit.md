# Reglas de Git — Proyecto de Agente de IA Aplicada

**Repositorio:** `Applied-AI-Agent-Project`
**Equipo:** Adriel S. Chaves Salazar · Daniel Duarte Cordero · Sebastián Hernández Bonilla

---

## Estrategia de ramas

```
master
  └── Stage1 | Stage2 | Stage3
        └── <NN><NombreRama>
```

Tres niveles. Sin `develop/**`, sin `release/**` y sin ramas personales.

---

## Ramas

### `master`
- **Propósito:** estado entregado y calificado del proyecto. Nunca se hace push directo.
- **Recibe PR de:** `Stage1`, `Stage2` y `Stage3` únicamente.
- **Aprobación:** **se requiere 1 aprobación.** Es el único lugar donde se exige.
- **Tipo de merge:** merge commit, para conservar la historia de la etapa.
- **Etiquetas:** cada merge se etiqueta (`v1.0.0-stage1`, `v2.0.0-stage2`, `v3.0.0-stage3`).

### `Stage1` / `Stage2` / `Stage3`
- **Propósito:** una rama por etapa del proyecto.
- **Recibe PR de:** ramas de trabajo únicamente.
- **Aprobación:** **ninguna.** Se abre el PR y se integra cuando el trabajo está listo.
- **Vida útil:** existe hasta que la etapa se entrega y se integra a `master`; después queda congelada, no se borra. Es la versión calificada.
- **Nunca se hace push directo.**

### Ramas de trabajo — `<NN><NombreRama>`
- **Propósito:** una rama por bloque de trabajo de `docx/01SeguimientoDeTareas/PlanDeDesarrollo.md`. Cada una agrupa todo lo necesario para cerrar los pendientes de ese bloque, no una tarea suelta.
- **Nombre:** exactamente el de la rama en el plan de desarrollo, con prefijo de dos dígitos y PascalCase, sin separadores.
- **Push directo:** permitido. Es la rama donde se trabaja.
- **Destino del PR:** la rama de la etapa a la que pertenece.
- **Se borra después del merge.**

---

## Resumen del flujo

```
04MainAIModelTrainingAndDevelopment
    │
    │  PR → sin aprobación
    ▼
Stage2
    │
    │  PR → 1 aprobación
    ▼
master  ← etiqueta v2.0.0-stage2
```

---

## Reglas de un vistazo

| Rama | ¿Push directo? | Destino del PR | ¿Aprobación? | ¿Etiqueta? |
|---|---|---|---|---|
| `master` | ❌ No | — | — | ✅ Sí |
| `Stage1` / `Stage2` / `Stage3` | ❌ No | `master` | ✅ 1 aprobación | ❌ No |
| `<NN><NombreRama>` | ✅ Sí | `Stage<N>` | ❌ No | ❌ No |

---

## Convención de nombres

### Ramas de etapa

```
Stage1
Stage2
Stage3
```

### Ramas de trabajo

`<número de dos dígitos><NombreEnPascalCase>`, idéntico al nombre que aparece en el plan de desarrollo. La numeración continúa entre etapas.

Etapa 1:

```
00TrackConfirmation
01LiteratureReview
02PaperAndDelivery
```

Etapa 2:

```
03DataCollectionAndEnvironmentSetup
04MainAIModelTrainingAndDevelopment
05FinalModelChecks
```

**Reglas:**
- Número de dos dígitos con cero a la izquierda, siempre.
- Sin espacios, guiones, guiones bajos ni barras dentro del nombre.
- Pocas ramas por etapa. Un trabajo que se cierra en menos de medio día no es una rama: va dentro de la rama a la que pertenece.
- La preparación del repositorio, de las herramientas o del entorno no es una rama aparte: va en la primera rama de la etapa.

---

## Trazabilidad

> **Los commits describen el cambio. Los PR indican qué pendientes del plan se cerraron.**

- **Commits:** tipo, alcance, qué cambió y por qué. Sin números de tarea.
- **Pull Requests:** el título nombra la rama de trabajo y la descripción lista los pendientes del plan de desarrollo que quedan cerrados.
- Al integrar una rama, sus pendientes se marcan como `[x]` en `PlanDeDesarrollo.md` dentro del mismo PR.

---

## Convención de mensajes de commit

Conventional Commits. El tipo y el alcance van en inglés, como dicta el estándar; el resumen y el cuerpo, en español.

```
<tipo>(<alcance>): <resumen breve>

<cuerpo opcional: qué y por qué, no cómo>
```

### Tipos

| Tipo | Uso |
|---|---|
| `docs` | Secciones del artículo, documentos Markdown, README |
| `refs` | Agregar, corregir o verificar entradas BibTeX |
| `feat` | Nueva capacidad de código (extractor, pipeline, exportación del modelo, herramienta del agente) |
| `fix` | Corrección de un error en código o de un dato en un documento |
| `exp` | Ejecución de un experimento, configuración o resultado registrado |
| `data` | Scripts de descarga, diccionario de datos, definiciones de preprocesamiento |
| `refactor` | Reestructuración sin cambio de comportamiento |
| `test` | Agregar o corregir pruebas, incluidos los invariantes de fuga |
| `build` | Dependencias, entorno de Colab, compilación LaTeX |
| `ci` | Configuración de integración continua |
| `chore` | Mantenimiento general |
| `style` | Solo formato |

### Alcances

- **Artículo y documentación:** `paper`, `intro`, `related`, `method`, `ethics`, `bib`, `table`, `gaps`, `baseline`, `repo`, `ai-decl`, `evidence`, `journal`
- **Ejes de revisión:** `axis-a`, `axis-b`, `axis-c`
- **Datos y protocolo:** `colab`, `ingest`, `features`, `eda`, `splits`, `leakage`, `protocol`
- **Modelado y evaluación:** `baselines`, `model`, `hpo`, `ablation`, `eval`, `xai`, `calib`, `export`
- **Etapa 3:** `agent`

### Reglas

- Modo imperativo, minúsculas, sin punto final, 72 caracteres como máximo.
- Un cambio lógico por commit.
- Sin números de tarea en los commits.
- **Nunca se versiona:** conjuntos de datos crudos, archivos Parquet, modelos entrenados, `.venv`, `node_modules`, artefactos de compilación LaTeX, credenciales (`kaggle.json`, `.env`, llaves de API).
- Cada integrante sube su propio trabajo. La autoría se califica por el historial de commits.

### Ejemplos

```
feat(features): extraer diferenciales de premios y puntos de vida

Construye las columnas propio menos oponente sobre la perspectiva
normalizada del jugador que actúa.
```

```
test(leakage): verificar intersección vacía de partidas entre particiones
```

```
exp(baselines): registrar B0 y B2 bajo el escenario A con semilla 42
```

```
data(eda): reportar prevalencia de la clase por fila
```

```
build(colab): fijar versión de scikit-learn y montar Drive al iniciar
```

```
refs(bib): completar la URL del conjunto de datos de Kaggle
```

---

## Convención de Pull Requests

### Título

```
<NN><NombreRama>: <resumen breve>
```

Ejemplo:

```
03DataCollectionAndEnvironmentSetup: tabla materializada y particiones agrupadas
```

### Plantilla de descripción

```markdown
## Resumen
Un párrafo: qué cierra esta rama y por qué.

## Pendientes cerrados
- [x] Pendiente copiado de PlanDeDesarrollo.md
- [x] Pendiente copiado de PlanDeDesarrollo.md

## Tipo de cambio
- [ ] Documentación o artículo
- [ ] Bibliografía
- [ ] Código
- [ ] Experimento o resultados
- [ ] Infraestructura

## Cambios
- Cambios principales
- Archivos agregados o modificados

## Cumplimiento académico
- [ ] Las referencias nuevas son arbitradas (revista o conferencia)
- [ ] Los DOI nuevos resuelven y su contenido corresponde a lo que se les atribuye
- [ ] Ningún preprint de arXiv sin justificación explícita
- [ ] Toda decisión técnica introducida está justificada por escrito
- [ ] Ningún conjunto de datos, modelo, credencial ni carpeta de dependencias versionado
- [ ] El uso de IA de este trabajo está reflejado en la declaración de uso de IA

## Prevención de fuga (ramas de código)
- [ ] El preprocesamiento se ajusta solo con entrenamiento
- [ ] Las pruebas de los invariantes pasan
- [ ] El conjunto de prueba no se usó para ninguna decisión

## Evidencia
- Enlace a la figura, registro o cuaderno que respalda cada afirmación
- El PDF compila sin errores (si se tocó el artículo)

## Lista de verificación
- [ ] Rama nombrada según la convención
- [ ] Commits según Conventional Commits
- [ ] Pendientes marcados en PlanDeDesarrollo.md
- [ ] Apunta a la rama de etapa correcta
```

### Reglas de los PR

- Una rama de trabajo, un PR. No mezclar trabajo no relacionado.
- **Squash merge** de rama de trabajo a rama de etapa.
- **Merge commit** de rama de etapa a `master`.
- El PR a `master` lista todos los pendientes cerrados durante la etapa.
- La aprobación hacia `master` la da un integrante que **no** haya hecho la mayor parte de la etapa.

---

## Reglas de exclusión

Como mínimo:

```gitignore
__pycache__/
*.py[cod]
.venv/
venv/
node_modules/
.ipynb_checkpoints/
*.aux
*.bbl
*.blg
*.log
*.out
*.fls
*.fdb_latexmk
*.synctex.gz
.env
kaggle.json
data/
*.parquet
*.joblib
*.pkl
```

Los conjuntos de datos, las tablas intermedias, los modelos entrenados y cualquier corpus descargado se excluyen: el repositorio guarda las instrucciones para obtenerlos, nunca los datos.

**Se versiona a propósito:** el `.bib`, los archivos de configuración con semillas fijas, las tablas de métricas, los registros de ejecución, los cuadernos con salidas y todos los documentos Markdown.

---

## Ritual de entrega de cada etapa

1. Congelamiento de contenido el día anterior a la entrega.
2. Prueba de clon limpio: clonar de cero, seguir solo el README y verificar que todo corre.
3. Verificar que el historial de commits muestra a los tres integrantes.
4. Verificar que la declaración de uso de IA tiene un bloque por integrante.
5. Abrir el PR `Stage<N>` → `master` con todos los pendientes cerrados, obtener 1 aprobación e integrar.
6. Etiquetar el merge commit.
7. Entregar el enlace del repositorio en TecDigital.