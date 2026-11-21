# Guía del ambiente

Qué se necesita para ejecutar el proyecto, dónde se ejecuta cada parte y en qué orden. El detalle de cada cuaderno está en [`notebooks/EjecucionDeLosCuadernos.md`](notebooks/EjecucionDeLosCuadernos.md), y el del agente y el simulador, en [`docx/05AmbienteDeDesarrollo/GuiaDelAgente.md`](docx/05AmbienteDeDesarrollo/GuiaDelAgente.md).

---

## 1. Dos lugares de ejecución

| Dónde | Qué se ejecuta ahí | Por qué |
|---|---|---|
| **Google Colab** | Cuadernos `00` a `07` y `09`: datos, modelos, evaluación final, perfil del dominio del agente y validación sin LLM | Necesitan las tablas del corpus (varios GB) y, algunos, horas de cómputo con RAM alta |
| **Tu PC** (Python 3.12 en `.venv`) | Agente (Claude Code, Claude Desktop y orquestador), servidor MCP, simulador gráfico y cuadernos `08` y `10` | Usan Claude con la membresía del equipo, que corre en la PC, y el simulador abre una página en tu navegador |

No se necesita GPU: todos los modelos son de scikit-learn. Para usar el agente no hace falta ejecutar nada en Colab: el modelo final y los archivos del agente ya están publicados en Kaggle.

---

## 2. Qué necesitas

| Requisito | Para qué | Cómo obtenerlo |
|---|---|---|
| **Cuenta de Kaggle y token** | Bajar los datos, el modelo y los resultados, y publicar los nuevos | kaggle.com → Settings → API → *Create New Token*. Cada integrante usa el suyo |
| **Acceso al dataset privado** `adrielchavessalazar/ptcg-wp-tablas` | Ahí viven las tablas, los modelos, los archivos del agente y todos los resultados | Pedir a Adriel que te agregue como colaborador. Sin acceso, ver la sección 6 |
| **Git** | Clonar el repositorio y subir cambios | Los commits se hacen desde tu PC, nunca desde Colab |
| **Google Colab** (Colab Pro para RAM alta) | Cuadernos de Colab (CPU, 8 núcleos y ~51 GiB) | colab.research.google.com, o VS Code con las extensiones de Jupyter y de Colab |
| **Python 3.12** en la PC | Agente, simulador y cuadernos de la PC | python.org o `winget install Python.Python.3.12`. Con versiones más nuevas no hay paquetes precompilados de `scikit-learn==1.7.2` |
| **Claude Code** con la cuenta de Claude del equipo (plan Pro o superior) | Conversar con el agente y correr el orquestador y el cuaderno `10` | `GuiaDelAgente.md`, sección 3.1. No hace falta clave de API |
| **VS Code** con las extensiones Python y Jupyter | Abrir los cuadernos `08` y `10` con el kernel de `.venv` | code.visualstudio.com |
| **MiKTeX o TeX Live con `latexmk`** (opcional) | Compilar el artículo y la bitácora | Ver la sección de compilación del [`README.md`](README.md) |

Las dependencias de Python están fijadas en `requirements.txt` (entre ellas `scikit-learn==1.7.2`, `shap==0.54.1`, `mcp==2.3.0` y `kaggle>=2.2.5`). Los cuadernos de Colab las instalan en su primera celda; en la PC se instalan una vez en `.venv` (sección 4).

**El token nunca se escribe en un cuaderno, en el repositorio ni en un chat.** Guárdalo en un archivo `secrets.txt` en la raíz del repositorio en tu PC (está en el `.gitignore`), con este formato:

```text
KAGGLE_API_TOKEN
<tu token>
```

Los cuadernos de Colab lo piden sin mostrarlo. En la PC, el agente lo lee de `secrets.txt` o de la variable `KAGGLE_API_TOKEN`. No actives el modo detallado (`VERBOSE`) de la herramienta `kaggle`: imprime el token.

---

## 3. Cómo se conectan las piezas

| Pieza | Qué guarda | ¿Se pierde al desconectarse? |
|---|---|---|
| **Tu PC + VS Code** | Tu copia del repositorio, `.venv`, los archivos del agente (`artefactos_agente/`) y los registros (`registros/`) | No |
| **GitHub** | Código, cuadernos, configuraciones, documentos y artículo | No |
| **Kaggle (dataset privado)** | Tablas Parquet, particiones, modelos, archivos del agente (`agente/`) y resultados, con SHA-256 y commit por archivo | No |
| **Servidor de Colab** | Copias de trabajo en `/content/repo`, `/content/datos` y `/content/resultados` | **Sí** |
| **Claude (membresía)** | Nada del proyecto: recibe la pregunta y los resultados de las herramientas para responder | — |

```text
Editas en tu PC → push a GitHub → Colab clona desde GitHub y baja de Kaggle → ejecuta → publica en Kaggle
Tu PC baja de Kaggle el modelo final → el agente y el simulador lo usan en tu PC
```

Colab solo ve lo que ya está en GitHub. Si un servidor se reinicia, basta volver a ejecutar el cuaderno desde arriba: lo publicado se baja de Kaggle y no se recalcula. Después de publicar algo nuevo, Kaggle tarda unos minutos en procesar la versión; si otra computadora no lo ve todavía, espera y vuelve a intentar.

---

## 4. Preparar la PC (una vez)

Desde la raíz del repositorio.

```powershell
# Windows (PowerShell)
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python --version   # debe decir 3.12
pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m ptcg_agente.artefactos
```

```bash
# Linux o macOS
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python -m ptcg_agente.artefactos
```

El último comando baja a `artefactos_agente/` el modelo final, su ficha, el perfil del dominio, el catálogo de cartas y las partidas de ejemplo, y comprueba el SHA-256 de cada archivo. Resultado esperado: `Listo: ... archivos verificados en ...`.

Después:

| Quiero… | Comando o paso | Detalle |
|---|---|---|
| Abrir el simulador | `python -m ptcg_agente.simulador --vacio` (con `PYTHONPATH=src`) | `GuiaDelAgente.md`, sección 8 |
| Conversar con el agente en Claude Code | Instalar Claude Code, activar `.venv` y escribir `claude` en la raíz | `GuiaDelAgente.md`, sección 3 |
| Usarlo desde Claude Desktop | Agregar el servidor `ptcg-victoria` a su configuración | `GuiaDelAgente.md`, sección 4 |
| Correr el orquestador | `python -m ptcg_agente.orquestador "pregunta" --archivo ...` | `GuiaDelAgente.md`, sección 7 |
| Ejecutar los cuadernos `08` o `10` | VS Code → kernel `.venv` → **Run All** | `EjecucionDeLosCuadernos.md`, sección 4 |

---

## 5. Cómo se ejecuta un cuaderno de Colab

1. Abre un cuaderno de `notebooks/` en Colab y elige **CPU** con **RAM alta**.
2. Ejecuta las celdas de arriba abajo. La primera celda clona el repositorio, instala `requirements.txt`, pide el token y baja de Kaggle lo que haga falta.
3. Cada celda que calcula algo revisa primero Kaggle. Si el resultado ya existe, lo baja; si falta, lo calcula y lo publica. No hay interruptores que activar.

Orden de los cuadernos:

```text
Modelo (Colab):     00_arranque → 01_exploracion → 02_baselines_B0_B1 → 03_baseline_B2
                    → 04_baseline_B3 → 05_baseline_B4 → 06_evaluacion_final
Agente (Colab):     07_agente → 09_validacion_agente
Agente (PC):        08_agente_orquestador → 10_validacion_llm
```

Celdas, tiempos y errores frecuentes: [`notebooks/EjecucionDeLosCuadernos.md`](notebooks/EjecucionDeLosCuadernos.md).

---

## 6. Sin acceso al dataset del equipo

El cuaderno `00_arranque` reconstruye las tablas desde el corpus público de Kaggle (días en `configs/dias.yaml`, unos 12 minutos por día). Para guardar los resultados, crea un dataset propio y pon su nombre en `configs/datos.yaml`. Después, los cuadernos 01 a 07 y 09 recalculan todo, incluidos el modelo final y los archivos del agente; los tiempos están en `EjecucionDeLosCuadernos.md`. Con esos archivos publicados, la PC se prepara igual que en la sección 4.

---

## 7. Pruebas

```bash
PYTHONPATH=src python -m pytest -q tests
```

Son 145 pruebas con datos sintéticos; no descargan nada. Comprueban los invariantes de fuga, las particiones, la evaluación, el almacén de Kaggle, el predictor, las herramientas y el verificador del agente, el orquestador (con un LLM de prueba), el servidor MCP, la batería de validación y el simulador. También corren como segunda celda de los cuadernos `00`, `06` y `07` a `10`: si fallan, la celda se detiene y no se calcula nada. En Windows pueden fallar por bloqueo de archivos; la referencia es Linux.

---

## 8. Documentos relacionados

| Documento | Contenido |
|---|---|
| [`notebooks/EjecucionDeLosCuadernos.md`](notebooks/EjecucionDeLosCuadernos.md) | Qué hace cada cuaderno, orden de celdas, tiempos y cómo reproducir los resultados del artículo |
| [`docx/05AmbienteDeDesarrollo/GuiaDelAgente.md`](docx/05AmbienteDeDesarrollo/GuiaDelAgente.md) | Instalación y uso del agente, del servidor MCP, del orquestador y del simulador |
| [`docx/05AmbienteDeDesarrollo/DiccionarioDeDatos.md`](docx/05AmbienteDeDesarrollo/DiccionarioDeDatos.md) | Qué es cada fila y columna, particiones y reglas para modelar |
| [`docx/03Evidencia/08-11-26_EticaDelDespliegue.md`](docx/03Evidencia/08-11-26_EticaDelDespliegue.md) | Riesgos, límites y uso aceptable del sistema |
| [`docx/00ReglasGit/ReglasGit.md`](docx/00ReglasGit/ReglasGit.md) | Ramas, commits y PR |
| [`docx/04Herramientas/HerramientasDeDesarrollo.md`](docx/04Herramientas/HerramientasDeDesarrollo.md) | Herramientas, librerías y herramientas de IA |