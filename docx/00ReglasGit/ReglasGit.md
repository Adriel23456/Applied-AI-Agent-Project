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
- **Etiquetas:** cada entrega se etiqueta (ver [Etiquetas](#etiquetas)).

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
- **Se conserva después del merge.** Los cuadernos clonan el repositorio por nombre de rama (variable `BRANCH` de su primera celda); borrar la rama rompería la reproducción de esos cuadernos.

---

## Ramas usadas en el proyecto

| Rama | Etapa | Responsable principal | Qué cerró | PR |
|---|---|---|---|---|
| `TrackConfirmation` | 1 | Equipo | Primera versión del repositorio (nombre anterior a la convención) | #1 |
| `00TrackConfirmation` | 1 | Equipo | Confirmación del track y del tema | #2 |
| `01LiteratureReview` | 1 | Cada integrante en su eje | Revisión de literatura por ejes A, B y C | #3 |
| `02PaperAndDelivery` | 1 | Equipo | Artículo preliminar y entrega de la Etapa 1 (con correcciones posteriores) | #4, #6, #7 |
| `Stage1` → `master` | 1 | Equipo | Integración de la Etapa 1 | #5 |
| `03DataCollectionAndEnvironmentSetup` | 2 | Adriel | Ingesta, tabla de estados, particiones, pruebas de fuga y entorno de Colab con Kaggle | #8 |
| `04MainAIModelTrainingAndDevelopment` | 2 | Daniel (entrenamiento) y Adriel (ejecución e infraestructura) | B0 a B4, búsqueda de hiperparámetros, LightGBM, ablaciones, H2 y modelo final | #9 |
| `05FinalModelChecks` | 2 | Sebastián (protocolo y cuaderno 06) y Adriel (ejecución) | Evaluación única en `test`, calibración, curvas, SHAP, errores y veredicto de H1 a H3 | #10 |
| `06PendientesDelArticulo` | 2 | Adriel | Correcciones del artículo, secciones de resultados, discusión y conclusiones, y documentación final de la etapa | Pendiente |

Las ramas de la Etapa 3 seguirán la numeración desde `07`.

---

## Resumen del flujo

```
05FinalModelChecks
    │
    │  PR → sin aprobación
    ▼
Stage2
    │
    │  PR → 1 aprobación
    ▼
master  ← etiqueta v2.0.0
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

`<número de dos dígitos><NombreEnPascalCase>`, idéntico al nombre que aparece en el plan de desarrollo. La numeración continúa entre etapas (ver la tabla de [ramas usadas](#ramas-usadas-en-el-proyecto)).

**Reglas:**
- Número de dos dígitos con cero a la izquierda, siempre.
- Sin espacios, guiones, guiones bajos ni barras dentro del nombre.
- Pocas ramas por etapa. Un trabajo que se cierra en menos de medio día no es una rama: va dentro de la rama a la que pertenece.
- La preparación del repositorio, de las herramientas o del entorno no es una rama aparte: va en la primera rama de la etapa.

---

## Etiquetas

| Etiqueta | Commit | Significado |
|---|---|---|
| `v1.0.0` | Merge de `02PaperAndDelivery` (#4) | Entrega de la Etapa 1 |
| `v1.0.1` | Merge de `02PaperAndDelivery` (#6) | Corrección posterior de la Etapa 1 |
| `v2.0.0` | Merge de `Stage2` a `master` | Entrega de la Etapa 2 |
| `v3.0.0` | Merge de `Stage3` a `master` | Entrega de la Etapa 3 |

Una corrección después de entregar sube el último número (`v2.0.1`).

---

## Trazabilidad

> **Los commits describen el cambio. Los PR indican qué pendientes del plan se cerraron.**

- **Commits:** tipo, alcance, qué cambió y por qué. Sin números de tarea.
- **Pull Requests:** el título nombra la rama de trabajo y la descripción lista los pendientes del plan de desarrollo que quedan cerrados.
- Al integrar una rama, sus pendientes se marcan como `[x]` en `PlanDeDesarrollo.md` dentro del mismo PR.
- **Resultados:** cada archivo de resultados publicado en Kaggle registra en el índice del dataset su SHA-256 y el commit del código que lo produjo. Así un resultado se rastrea hasta su commit aunque no esté versionado en Git.

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
- **Datos y protocolo:** `colab`, `ingest`, `features`, `eda`, `splits`, `leakage`, `protocol`, `store`
- **Modelado y evaluación:** `baselines`, `model`, `hpo`, `ablation`, `eval`, `xai`, `calib`, `export`
- **Etapa 3:** `agent`

### Reglas

- Modo imperativo, minúsculas, sin punto final, 72 caracteres como máximo.
- Un cambio lógico por commit.
- Sin números de tarea en los commits.
- **Nunca se versiona:** conjuntos de datos crudos, archivos Parquet, modelos entrenados (`*.joblib`), la carpeta `results/`, `.venv`, artefactos de compilación LaTeX, credenciales (`secrets.txt`, `kaggle.json`, `.env`, tokens).
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
exp(eval): registrar la evaluación única en test de los escenarios A, B y C
```

```
data(eda): reportar prevalencia de la clase por fila
```

```
build(colab): fijar versión de scikit-learn y leer el token de Kaggle sin mostrarlo
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
- **Merge commit** de rama de trabajo a rama de etapa y de rama de etapa a `master`. No se usa *squash*: juntaría los commits de varios integrantes en uno solo y borraría la autoría que se califica.
- El PR a `master` lista todos los pendientes cerrados durante la etapa.
- La aprobación hacia `master` la da un integrante que **no** haya hecho la mayor parte de la etapa.

---

## Reglas de exclusión

El `.gitignore` del repositorio parte de la plantilla de Python y agrega, como mínimo:

```gitignore
__pycache__/
.venv/
.ipynb_checkpoints
*.log
.env
secrets.txt
*.joblib
results/
```

Los artefactos de compilación LaTeX (`*.aux`, `*.bbl`, `*.fls`, etc.) tienen su propio `.gitignore` dentro de cada proyecto LaTeX.

**Dónde viven los datos y resultados.** Las tablas procesadas, las particiones, los modelos entrenados y todos los resultados (CSV, JSON, figuras) viven en el dataset privado de Kaggle `adrielchavessalazar/ptcg-wp-tablas`, nunca en Git. El repositorio guarda el código y las configuraciones para reconstruirlos.

**Se versiona a propósito:** el código de `src/`, las pruebas, los archivos de `configs/` con semillas fijas, el `.bib`, el PDF del artículo, el cuaderno `06_evaluacion_final.ipynb` con sus salidas y todos los documentos Markdown.

---

## Ritual de entrega de cada etapa

1. Congelamiento de contenido el día anterior a la entrega.
2. Prueba de clon limpio: clonar de cero, seguir solo el README y verificar que todo corre.
3. Verificar que el historial de commits muestra a los tres integrantes.
4. Verificar que la declaración de uso de IA tiene un bloque por integrante.
5. Abrir el PR `Stage<N>` → `master` con todos los pendientes cerrados, obtener 1 aprobación e integrar.
6. Etiquetar el merge commit.
7. Entregar el enlace del repositorio en TecDigital.