# Proyecto de Agente de IA Aplicada

Proyecto semestral del curso **IC-6200 — Inteligencia Artificial**, Escuela de Ingeniería en Computación, Instituto Tecnológico de Costa Rica. II Semestre, 2026.

Una solución de IA aplicada construida bajo la metodología de la investigación aplicada y consumida de forma verificable por un agente inteligente. El proyecto se desarrolla durante 16 semanas en tres etapas obligatorias.

---

## Estado

| Etapa | Entregable | Fecha | Peso | Estado |
| --- | --- | --- | --- | --- |
| **Etapa 1** | Estado del arte, análisis del problema y artículo IEEE preliminar | 06/09/2026 | 30 % | Completa |
| **Etapa 2** | Cuaderno con el ciclo metodológico: datos, baselines, modelo, explicabilidad y evaluación | Semana 10 | 45 % | En curso |
| **Etapa 3** | Agente inteligente funcional y artículo final | Semana 16 | 25 % | No iniciada |

**Track:** Track A — Aprendizaje automático clásico sobre datos tabulares.
**Tema:** Estimación de la probabilidad de victoria a partir del estado de juego en el Pokémon Trading Card Game: un estudio de clasificación tabular con control explícito de fuga de información.
**Conjunto de datos:** repeticiones del PTCG AI Battle Challenge (Kaggle).

### Etapa 2 en curso

La Etapa 2 ejecuta el diseño declarado en el artículo de la Etapa 1. Se desarrolla en Google Colab y comprende:

- Ingesta del corpus y construcción de la tabla, con una fila por estado del jugador que actúa.
- Particiones agrupadas por partida bajo tres escenarios: partidas nuevas, periodos posteriores y mazos reservados.
- Pruebas automáticas que impiden la fuga de información.
- Escalera de modelos: probabilidad a priori, heurística de dominio, regresión logística, árboles y potenciación del gradiente.
- Búsqueda sistemática de hiperparámetros con validación cruzada agrupada.
- Explicabilidad con SHAP y calibración de probabilidades.
- Comparación contra los baselines internos y el baseline de literatura.
- Modelo final exportado para que el agente de la Etapa 3 lo consuma.

Los pendientes por rama están en `docx/01SeguimientoDeTareas/PlanDeDesarrollo.md`.

---

## Equipo

| Integrante | Carné | Eje de revisión |
| --- | --- | --- |
| Adriel S. Chaves Salazar | 2021031465 | Eje B — técnicas del track seleccionado |
| Daniel Duarte Cordero | 2022012866 | Eje A — problema y dominio |
| Sebastián Hernández Bonilla | 2022093651 | Eje C — conjunto de datos |

**Profesor:** Kenneth Roberto Obando Rodríguez

La autoría individual se determina por el historial de commits. Los archivos comunes cuentan como autoría compartida.

---

## Guía del repositorio

| Ruta | Contenido |
| --- | --- |
| `docx/00ReglasGit/` | Convenciones de ramas, commits y PR |
| `docx/01SeguimientoDeTareas/` | Plan de desarrollo con los pendientes por rama |
| `docx/02Papers/` | Literatura revisada por integrante y fuentes LaTeX del artículo |
| `docx/02Papers/00MainPaper/` | Artículo IEEE: `MainPaper.tex`, secciones y bibliografía |
| `docx/03Evidence/` | Notas de reunión, acuerdos, hitos y bitácora de trabajo |
| `docx/03Evidence/01UsoDeIA/` | Declaración de uso de IA por etapa |
| `docx/04Herramientas/` | Herramientas de búsqueda bibliográfica y de conjuntos de datos |

Algunas carpetas incluyen un `Contenido.md` que describe su propósito.

---

## Compilación del artículo

Requiere una distribución TeX con `IEEEtran` (MiKTeX o TeX Live) y `latexmk`.

```bash
cd docx/02Papers/00MainPaper
latexmk -C
latexmk -pdf MainPaper.tex
```

Salida: `MainPaper.pdf`.

Para verificar que no quedan marcadores pendientes, redefina la macro `\todo` en `preamble.tex` como `\newcommand{\todo}[1]{}` y recompile: toda sección que aparezca vacía está sin terminar.

---

## Compilación de la bitácora de trabajo

```bash
cd docx/03Evidence/00BitacoraDeTrabajo
latexmk -C
latexmk -pdf BitacoraDeTrabajo.tex
```

---

## Reproducción de los experimentos

> En desarrollo durante la Etapa 2.

[POR COMPLETAR: preparación del entorno en Colab, instalación de dependencias, credencial de Kaggle, descarga del conjunto de datos, construcción de la tabla y la orden exacta que reproduce cada cifra reportada.]

**Contrato de reproducibilidad.** Todo resultado reportado debe poder reproducirlo un tercero siguiendo solo esta sección, sin contactar al equipo. Las semillas están fijadas y versionadas. Las configuraciones se guardan en archivos, no se pasan como argumentos sueltos. Los datos crudos, las tablas intermedias y las credenciales nunca se versionan; solo las instrucciones para obtenerlos.

---

## Convenciones

* **Git:** Ver `docx/00ReglasGit/ReglasGit.md`. Tres niveles de ramas: `master` → `Stage<N>` → `<NN><NombreRama>`. PR para cada integración; la aprobación solo se exige para los merges a `master`.
* **Bibliografía:** Solo BibTeX, con claves en formato `autor_palabraclave_anio`. Fuentes arbitradas de revista o conferencia; antes de versionar una entrada, su DOI debe resolver y su contenido debe corresponder a lo que se le atribuye.
* **Documentación:** Markdown dentro del repositorio. El artículo es el entregable; el Markdown es el registro de trabajo.

---

## Licencia

MIT. Ver `LICENSE`.

La licencia cubre el código y la documentación propios del repositorio. No se extiende a conjuntos de datos de terceros ni a los PDF de los artículos revisados guardados en `docx/02Papers/`, que conservan su licencia y términos originales.