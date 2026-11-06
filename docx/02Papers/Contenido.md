# Qué contiene — `02Papers`

Todo lo bibliográfico y todo lo escrito para el artículo.

## Contenido

### `00MainPaper/`: artículo principal

Artículo IEEE del proyecto, en LaTeX. Es el entregable de las Etapas 1 y 2.

| Ruta | Contenido |
|---|---|
| `MainPaper.tex` | Archivo principal: título, autores, resumen y orden de las secciones |
| `MainPaper.pdf` | Versión compilada del artículo |
| `preamble.tex` | Paquetes, colores y macros comunes |
| `sec/01introduccion.tex` | Juego, motivación, pregunta de investigación, hipótesis y objetivos |
| `sec/02trabajos_relacionados.tex` | Revisión de literatura en los tres ejes y brechas |
| `sec/03baseline_literatura.tex` | Baseline de literatura (Hearthstone, AUC 0.78–0.80) y su comparabilidad |
| `sec/04metodologia.tex` | Formalización, protocolo, escenarios A/B/C, métricas y plan de modelos |
| `sec/05analisis_tecnico.tex` | Análisis exploratorio, diccionario, calidad de datos y prevención de fuga |
| `sec/07resultados.tex` | Ejecución del protocolo, desviaciones y resultados en prueba |
| `sec/08discusion.tex` | Respuesta a la pregunta, hipótesis, hallazgos de SHAP, objetivos y limitaciones |
| `sec/06etica.tex` | Consideraciones éticas |
| `sec/09conclusiones.tex` | Conclusiones y trabajo futuro |
| `sec/99referencias.bib` | Bibliografía verificada contra fuente primaria |
| `tab/tabla_comparativa.tex` | Tabla comparativa de la literatura |
| `img/` | Figuras: ilustración del juego y resultados de la evaluación final (`res_*.png`, exportadas del cuaderno 06) |

El orden de las secciones en el PDF es: introducción, trabajos relacionados, baseline de literatura, metodología, análisis técnico, resultados, discusión, ética y conclusiones.

Compilación:

```bash
cd docx/02Papers/00MainPaper
latexmk -pdf MainPaper.tex
```

Requiere una distribución TeX con `IEEEtran` (MiKTeX o TeX Live).

### Carpetas por eje: revisión de literatura de la Etapa 1

| Carpeta | Integrante | Eje |
|---|---|---|
| `01Daniel_AxisA/` | Daniel Duarte Cordero | Eje A: problema y dominio |
| `02Adriel_AxisB/` | Adriel S. Chaves Salazar | Eje B: técnicas del *track* |
| `03Sebastian_AxisC/` | Sebastián Hernández Bonilla | Eje C: conjunto de datos |

Cada carpeta guarda la revisión individual de su eje (en LaTeX), su archivo `.bib` y, en las carpetas A y B, los artículos leídos (`MyPapers/`). Cada integrante organiza su carpeta como prefiera.

## Reglas

*   Un artículo solo entra al `.bib` principal cuando su DOI resuelve y su contenido corresponde a lo que se le atribuye.
*   Toda referencia citada en el artículo principal tiene su fuente documentada en la carpeta de eje de quien la revisó.
*   Toda cifra del artículo sale de una celda ejecutada por el equipo; las de la Etapa 2 están trazadas en `docx/03Evidencia/04-11-26_ResultadosEvaluacionFinal.md` y en el cuaderno `notebooks/06_evaluacion_final.ipynb`.
*   Los PDF de artículos de terceros conservan su licencia original.