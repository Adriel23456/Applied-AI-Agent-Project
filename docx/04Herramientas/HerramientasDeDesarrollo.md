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

### Agente (Etapa 3)

| Herramienta | Para qué se usó | Enlace |
|---|---|---|
| Python 3.12 en `.venv` (PC) | Correr el agente, el servidor MCP, el simulador y los cuadernos `08` y `10` con la misma versión de Colab | https://www.python.org/downloads/ |
| Claude Code | Interfaz del agente con el servidor MCP del proyecto, subagentes (`.claude/agents/`) y comando `/consulta-ptcg`; en modo sin interfaz (`claude -p`), motor del planificador y del redactor del orquestador | https://docs.claude.com/en/docs/claude-code/overview |
| Claude Desktop | Interfaz alternativa con el mismo servidor MCP | https://claude.ai/download |
| Model Context Protocol (MCP) | Protocolo con el que Claude llama a las herramientas del modelo (servidor `ptcg-victoria`) | https://modelcontextprotocol.io/ |
| Navegador web | Mostrar el simulador gráfico (página local en `http://127.0.0.1:8765/`) | — |
| VS Code con las extensiones Python y Jupyter | Ejecutar los cuadernos de la PC con el kernel de `.venv` | https://code.visualstudio.com/ |

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
| pytest | Pruebas de fuga, particiones, evaluación, agente, validación y simulador (145 en total) |
| kaggle 2.2.5 o superior | Descarga y publicación de datos y resultados. La 2.0.2 de Colab no podía crear versiones (error 400) |
| mcp 2.3.0 | Servidor MCP del agente (`src/ptcg_agente/servidor_mcp.py`) |
| Biblioteca estándar de Python (`http.server`) y JavaScript sin librerías | Simulador gráfico, sin dependencias nuevas |

### Herramientas de IA

| Herramienta | Etapa | Uso |
|---|---|---|
| Claude (Anthropic) | 1, 2 y 3 | Etapa 1: encuadre del tema, revisión de literatura y redacción. Etapa 2: código de datos y entorno (Adriel), entrenamiento de B0 a B4 (Daniel), protocolo y cuaderno de evaluación final (Sebastián, con Claude Code), y redacción del artículo. Etapa 3: agente, validación, simulador, ética y artículo final (Adriel); revisión del proceso y del funcionamiento y apoyo en las evaluaciones (Daniel y Sebastián) |
| Claude como parte del sistema | 3 | Planificador y redactor del agente (`claude -p`) e interfaz de Claude Code y Claude Desktop. Es objeto de estudio: se validó con el protocolo de la rama 08 |
| ChatGPT | 1 | Clasificación de referencias y organización de ideas |
| Consensus | 1 | Búsqueda de literatura revisada por pares |

El detalle de qué hizo cada herramienta y qué revisó el equipo está en `docx/03Evidencia/01UsoDeIA/` (`Etapa1UsoDeIA.md`, `Etapa2UsoDeIA.md` y `Etapa3UsoDeIA.md`).