## Herramientas de desarrollo

### Datos y ejecución

| Herramienta | Para qué se usó | Enlace |
|---|---|---|
| Google Colab (CPU + RAM alta, 8 núcleos y ~51 GiB) | Ejecutar todos los cuadernos | https://colab.research.google.com/ |
| VS Code con las extensiones de Jupyter y de Colab | Editar el código y conectarse al servidor de Colab | https://code.visualstudio.com/ |
| Corpus público del PTCG AI Battle Challenge (un dataset por día; ejemplo del 18 jun) | Datos crudos de las partidas | https://www.kaggle.com/datasets/kaggle/pokemon-tcg-ai-battle-episodes-2026-06-18 |
| Dataset privado del equipo `ptcg-wp-tablas` | Tablas procesadas, modelos y resultados | https://www.kaggle.com/datasets/adrielchavessalazar/ptcg-wp-tablas |
| GitHub | Código, cuadernos, documentación y artículo | https://github.com/Adriel23456/Applied-AI-Agent-Project |
| MiKTeX o TeX Live con `latexmk` | Compilar el artículo y la bitácora | https://miktex.org/ |

### Librerías principales

Versiones fijadas en `requirements.txt`.

| Librería | Uso |
|---|---|
| pandas, numpy, pyarrow | Tablas y archivos Parquet |
| scikit-learn 1.7.2 | B0 a B4, `Pipeline`, validación agrupada y calibración |
| Optuna 4.6.0 | Búsqueda bayesiana de hiperparámetros de B4 |
| LightGBM 4.6.0 | Verificación de que B4 no depende de la librería |
| SHAP 0.54.1 | Explicabilidad del modelo final |
| matplotlib | Figuras |
| pytest | Pruebas de fuga, particiones y evaluación |
| kaggle | Descarga y publicación de datos y resultados |

### Herramientas de IA

| Herramienta | Etapa | Uso |
|---|---|---|
| Claude (Anthropic) | 1 y 2 | Etapa 1: encuadre del tema, revisión de literatura y redacción. Etapa 2: código de datos y entorno (Adriel), entrenamiento de B0 a B4 (Daniel), protocolo y cuaderno de evaluación final (Sebastián, con Claude Code), y redacción del artículo |
| ChatGPT | 1 | Clasificación de referencias y organización de ideas |
| Consensus | 1 | Búsqueda de literatura revisada por pares |

El detalle de qué hizo cada herramienta y qué revisó el equipo está en `docx/03Evidencia/01UsoDeIA/` (`Etapa1UsoDeIA.md` y `Etapa2UsoDeIA.md`).