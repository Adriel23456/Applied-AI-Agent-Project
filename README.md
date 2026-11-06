# Proyecto de Agente de IA Aplicada

Proyecto semestral del curso **IC-6200 — Inteligencia Artificial**, Escuela de Ingeniería en Computación, Instituto Tecnológico de Costa Rica. II Semestre, 2026.

Una solución de IA aplicada construida bajo la metodología de la investigación aplicada y consumida de forma verificable por un agente inteligente. El proyecto se desarrolla durante 16 semanas en tres etapas.

**Track:** Track A — Aprendizaje automático clásico sobre datos tabulares.
**Tema:** Estimación de la probabilidad de victoria a partir del estado de juego en el Pokémon Trading Card Game: un estudio de clasificación tabular con control explícito de fuga de información.
**Datos:** repeticiones del PTCG AI Battle Challenge (Kaggle), diez días entre el 17 de junio y el 22 de julio de 2026.

---

## Estado

| Etapa | Entregable | Fecha | Peso | Estado |
| --- | --- | --- | --- | --- |
| **Etapa 1** | Estado del arte, análisis del problema y artículo IEEE preliminar | 06/09/2026 | 30 % | Completa |
| **Etapa 2** | Datos, baselines, modelo, explicabilidad, evaluación y artículo con metodología y resultados | Semana 10 | 45 % | Completa |
| **Etapa 3** | Agente inteligente funcional y artículo final | Semana 16 | 25 % | No iniciada |

### Resultados de la Etapa 2

- **Datos:** 55 196 partidas y 7 286 386 estados utilizables, con 62 características públicas por estado.
- **Modelo principal:** B4, potenciación del gradiente (`HistGradientBoostingClassifier`) con búsqueda de hiperparámetros en Optuna y validación cruzada agrupada por partida.
- **AUC en prueba:** 0.833 en partidas nuevas (A), 0.789 en días posteriores (B) y 0.787 en arquetipos de mazo nuevos (C). Supera a las cuatro referencias (B0 a B3) en los tres escenarios.
- **Hipótesis:**
  - H1 sostenida: la predicción mejora con la partida, de 0.68 al inicio a 0.94 al final.
  - H2 no sostenida en general: refutada en A, sostenida en B y C.
  - H3 refutada: con el tiempo, el ordenamiento se degrada más que la calibración.
- **Módulo de grupo de tres:** calibración de probabilidades. B4 ya está calibrado en A (ECE 0.002); en B, la recalibración isotónica baja el ECE de 0.037 a 0.018.
- **Modelo final para la Etapa 3:** B4 entrenado en A, en `ptcg_wp.predictor.PredictorVictoria`.

---

## Por dónde empezar

| Quiero… | Ir a |
| --- | --- |
| Leer el artículo | [`docx/02Papers/00MainPaper/MainPaper.pdf`](docx/02Papers/00MainPaper/MainPaper.pdf) |
| Preparar el ambiente y ejecutar el proyecto | [`GuiaDeAmbiente.md`](GuiaDeAmbiente.md) |
| Ver qué hace cada cuaderno y reproducir los resultados del artículo | [`notebooks/EjecucionDeLosCuadernos.md`](notebooks/EjecucionDeLosCuadernos.md) |
| Entender los datos: filas, columnas, particiones y reglas para modelar | [`docx/05AmbienteDeDesarrollo/DiccionarioDeDatos.md`](docx/05AmbienteDeDesarrollo/DiccionarioDeDatos.md) |
| Ver los resultados de la evaluación final con su interpretación | [`docx/03Evidencia/04-11-26_ResultadosEvaluacionFinal.md`](docx/03Evidencia/04-11-26_ResultadosEvaluacionFinal.md) |
| Ver el protocolo de evaluación, escrito antes de abrir `test` | [`docx/03Evidencia/02-11-26_ProtocoloEvaluacionFinal.md`](docx/03Evidencia/02-11-26_ProtocoloEvaluacionFinal.md) |
| Ver el plan de trabajo y los pendientes por rama | [`docx/01SeguimientoDeTareas/PlanDeDesarrollo.md`](docx/01SeguimientoDeTareas/PlanDeDesarrollo.md) |
| Ver la declaración de uso de IA | [`docx/03Evidencia/01UsoDeIA/`](docx/03Evidencia/01UsoDeIA/) (`Etapa1UsoDeIA.md` y `Etapa2UsoDeIA.md`) |
| Conocer las reglas de ramas, commits y PR | [`docx/00ReglasGit/ReglasGit.md`](docx/00ReglasGit/ReglasGit.md) |
| Ver las herramientas usadas, incluidas las de IA | [`docx/04Herramientas/`](docx/04Herramientas/) |

---

## Equipo

| Integrante | Carné | Eje de revisión (Etapa 1) | Trabajo principal (Etapa 2) |
| --- | --- | --- | --- |
| Adriel S. Chaves Salazar | 2021031465 | Eje B — técnicas del track | Datos, entorno, infraestructura, ejecución de experimentos y artículo |
| Daniel Duarte Cordero | 2022012866 | Eje A — problema y dominio | Entrenamiento de B0 a B4 |
| Sebastián Hernández Bonilla | 2022093651 | Eje C — conjunto de datos | Protocolo y cuaderno de evaluación final |

**Profesor:** Kenneth Roberto Obando Rodríguez

La autoría individual se determina por el historial de commits. Los archivos comunes cuentan como autoría compartida.

---

## Estructura del repositorio

| Ruta | Contenido |
| --- | --- |
| `src/ptcg_wp/` | Código del proyecto: ingesta, características, particiones, modelos, evaluación, almacén en Kaggle y predictor final |
| `notebooks/` | Cuadernos `00` a `06`, que ejecutan el código en Colab |
| `tests/` | Pruebas automáticas (fuga, particiones, evaluación y almacén) |
| `configs/` | Días del corpus, particiones y dataset de Kaggle |
| `docx/00ReglasGit/` | Convenciones de ramas, commits y PR |
| `docx/01SeguimientoDeTareas/` | Plan de desarrollo con los pendientes por rama |
| `docx/02Papers/00MainPaper/` | Artículo IEEE en LaTeX: `MainPaper.tex`, secciones en `sec/`, figuras en `img/` y bibliografía |
| `docx/02Papers/0X_*_Axis*/` | Literatura revisada por cada integrante |
| `docx/03Evidencia/` | Protocolos, auditorías, resultados, notas de reunión y bitácora de trabajo |
| `docx/03Evidencia/01UsoDeIA/` | Declaración de uso de IA por etapa |
| `docx/04Herramientas/` | Herramientas de búsqueda, de desarrollo y de IA |
| `docx/05AmbienteDeDesarrollo/` | Diccionario de datos |

Algunas carpetas incluyen un `Contenido.md` que describe su propósito.

Los datos, los modelos entrenados y los resultados no están en Git: viven en el dataset privado de Kaggle `adrielchavessalazar/ptcg-wp-tablas`, con el SHA-256 y el commit de cada archivo. Ver [`GuiaDeAmbiente.md`](GuiaDeAmbiente.md).

---

## Ejecución en breve

1. Consigue un token de Kaggle y acceso al dataset del equipo.
2. Abre un cuaderno de `notebooks/` en Google Colab con CPU y RAM alta.
3. Ejecútalo de arriba abajo: la primera celda prepara todo y cada celda baja de Kaggle lo que ya existe.

Para obtener las cifras del artículo, ejecuta `notebooks/06_evaluacion_final.ipynb`. Detalle completo: [`GuiaDeAmbiente.md`](GuiaDeAmbiente.md) y [`notebooks/EjecucionDeLosCuadernos.md`](notebooks/EjecucionDeLosCuadernos.md).

**Contrato de reproducibilidad.** Todo resultado reportado debe poder reproducirlo un tercero siguiendo esas dos guías, sin contactar al equipo. Las semillas (`SEED = 2026`) y las configuraciones están versionadas en `configs/`. Los datos crudos, las tablas intermedias y las credenciales nunca se versionan; solo las instrucciones para obtenerlos.

---

## Compilación del artículo

Requiere una distribución TeX con `IEEEtran` (MiKTeX o TeX Live) y `latexmk`.

```bash
cd docx/02Papers/00MainPaper
latexmk -C
latexmk -pdf MainPaper.tex
```

Salida: `MainPaper.pdf`. Las secciones están en `sec/` (`01introduccion.tex` a `09conclusiones.tex`) y la bibliografía en `sec/99referencias.bib`.

Para verificar que no quedan marcadores pendientes, redefina la macro `\todo` en `preamble.tex` como `\newcommand{\todo}[1]{}` y recompile: toda sección que aparezca vacía está sin terminar.

### Bitácora de trabajo

```bash
cd docx/03Evidencia/00BitacoraDeTrabajo
latexmk -C
latexmk -pdf BitacoraDeTrabajo.tex
```

---

## Convenciones

* **Git:** ver [`docx/00ReglasGit/ReglasGit.md`](docx/00ReglasGit/ReglasGit.md). Tres niveles de ramas: `master` → `Stage<N>` → `<NN><NombreRama>`. PR para cada integración; la aprobación solo se exige para los merges a `master`.
* **Bibliografía:** solo BibTeX, con claves en formato `autor_palabraclave_anio`. Fuentes arbitradas de revista o conferencia; antes de versionar una entrada, su DOI debe resolver y su contenido debe corresponder a lo que se le atribuye.
* **Documentación:** Markdown dentro del repositorio. El artículo es el entregable; el Markdown es el registro de trabajo.

---

## Licencia

MIT. Ver `LICENSE`.

La licencia cubre el código y la documentación propios del repositorio. No se extiende a conjuntos de datos de terceros ni a los PDF de los artículos revisados guardados en `docx/02Papers/`, que conservan su licencia y términos originales.