# Qué contiene — `02Papers`

Todo lo bibliográfico y todo lo escrito para el artículo.

## Contenido

### `00MainPaper/`: artículo principal

Artículo IEEE del proyecto, en LaTeX. Es el entregable de las tres etapas; la versión de la Etapa 3 suma el agente, su validación y la ética del despliegue.

| Ruta | Contenido |
|---|---|
| `MainPaper.tex` | Archivo principal: título, autores, resumen, palabras clave y orden de las secciones |
| `MainPaper.pdf` | Versión compilada del artículo (29 páginas) |
| `preamble.tex` | Paquetes, colores y macros comunes |
| `sec/01introduccion.tex` | Juego, motivación, pregunta de investigación, hipótesis, siete objetivos y cuatro contribuciones |
| `sec/02trabajos_relacionados.tex` | Revisión de literatura en los tres ejes y brechas |
| `sec/03baseline_literatura.tex` | Baseline de literatura (Hearthstone, AUC 0.78–0.80) y su comparabilidad |
| `sec/04metodologia.tex` | Formalización, protocolo, escenarios A/B/C, métricas y plan de modelos |
| `sec/05analisis_tecnico.tex` | Análisis exploratorio, diccionario, calidad de datos y prevención de fuga |
| `sec/07resultados.tex` | Ejecución del protocolo, desviaciones y resultados del modelo en prueba |
| `sec/10agente.tex` | Integración y validación del agente: arquitectura, protocolo, resultados N1, N2 y validación humana, fragilidad y figuras del agente en Claude Code y del simulador |
| `sec/08discusion.tex` | Respuesta a la pregunta, hipótesis, hallazgos de SHAP, qué aporta el agente, objetivos y limitaciones |
| `sec/06etica.tex` | Ética del despliegue: datos sensibles, riesgos, mitigaciones verificables y límites declarados |
| `sec/09conclusiones.tex` | Conclusiones y trabajo futuro |
| `sec/99referencias.bib` | Bibliografía verificada contra fuente primaria |
| `tab/tabla_comparativa.tex` | Tabla comparativa de la literatura |
| `img/` | Figuras: ilustración del juego, resultados de la evaluación final (`res_auc_por_turno.png`, `res_fiabilidad.png` y `res_shap.png`, exportadas del cuaderno 06) y evidencia del agente (`res_agente_claude.png`, recorte de `docx/03Evidencia/08-11-26_RegistroSesionClaudeCode.png`, y `res_simulador.png`, copia de `08-11-26_SimuladorPartida87363568.png`) |

El orden de las secciones en el PDF es: introducción, trabajos relacionados, baseline de literatura, metodología, análisis técnico, resultados, agente, discusión, ética y conclusiones. Los nombres de archivo conservan su número original: `10agente.tex` va después de `07resultados.tex`.

Figuras de la Etapa 3: Fig. 11 (flujo de una consulta, dibujada en TikZ), Fig. 12 (consulta real en Claude Code) y Fig. 13 (simulador gráfico).

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
*   Toda cifra del artículo sale de una celda ejecutada por el equipo. Las de la Etapa 2 están trazadas en `docx/03Evidencia/04-11-26_ResultadosEvaluacionFinal.md` y en el cuaderno `notebooks/06_evaluacion_final.ipynb`; las de la Etapa 3, en `docx/03Evidencia/08-11-26_ResultadosValidacionAgente.md`, `08-11-26_ValidacionHumanaSimulador.md` y `08-11-26_EticaDelDespliegue.md`, y en los cuadernos `07` a `10`.
*   Los PDF de artículos de terceros conservan su licencia original.