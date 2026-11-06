# Guía del ambiente

Qué se necesita para ejecutar el proyecto y en qué orden. El detalle de cada cuaderno está en [`notebooks/EjecucionDeLosCuadernos.md`](notebooks/EjecucionDeLosCuadernos.md).

---

## 1. Qué necesitas

| Requisito | Para qué | Cómo obtenerlo |
|---|---|---|
| **Cuenta de Kaggle y token** | Bajar los datos y los resultados, y publicar los nuevos | kaggle.com → Settings → API → *Create New Token*. Cada integrante usa el suyo |
| **Acceso al dataset privado** `adrielchavessalazar/ptcg-wp-tablas` | Ahí viven las tablas, los modelos y todos los resultados | Pedir a Adriel que te agregue como colaborador. Sin acceso, ver la sección 4 |
| **Google Colab** (recomendado; Colab Pro para RAM alta) | Ejecutar los cuadernos en un servidor con CPU y RAM alta (8 núcleos, ~51 GiB) | colab.research.google.com, o VS Code con las extensiones de Jupyter y de Colab |
| **Git** | Clonar el repositorio y subir cambios | Los commits se hacen desde tu PC, nunca desde Colab |
| **Dependencias de Python** | Código del proyecto | `requirements.txt`. Cada cuaderno las instala en su primera celda |
| **MiKTeX o TeX Live con `latexmk`** (opcional) | Compilar el artículo | Ver la sección de compilación del [`README.md`](README.md) |

No se necesita GPU: todos los modelos son de scikit-learn.

**El token nunca se escribe en un cuaderno, en el repositorio ni en un chat.** Guárdalo en un archivo `secrets.txt` en tu PC (está en el `.gitignore`), con este formato:

```text
KAGGLE_API_TOKEN
<tu token>
```

La primera celda de cada cuaderno lo pide sin mostrarlo.

---

## 2. Cómo se conectan las piezas

| Pieza | Qué guarda | ¿Se pierde al desconectarse? |
|---|---|---|
| **Tu PC + VS Code** | Tu copia del repositorio | No |
| **GitHub** | Código, cuadernos, configuraciones, documentos y artículo | No |
| **Kaggle (dataset privado)** | Tablas Parquet, particiones, modelos y resultados, con SHA-256 y commit por archivo | No |
| **Servidor de Colab** | Copias de trabajo en `/content/repo`, `/content/datos` y `/content/resultados` | **Sí** |

```text
Editas en tu PC → push a GitHub → Colab clona desde GitHub y baja de Kaggle → ejecuta → publica en Kaggle
```

Colab solo ve lo que ya está en GitHub. Si un servidor se reinicia, basta volver a ejecutar el cuaderno desde arriba: lo publicado se baja de Kaggle y no se recalcula.

---

## 3. Cómo se ejecuta todo

1. Abre un cuaderno de `notebooks/` en Colab y elige **CPU** con **RAM alta**.
2. Ejecuta las celdas de arriba abajo. La primera celda clona el repositorio, instala `requirements.txt`, pide el token y baja de Kaggle lo que haga falta.
3. Cada celda que calcula algo revisa primero Kaggle. Si el resultado ya existe, lo baja; si falta, lo calcula y lo publica. No hay interruptores que activar.

Orden de los cuadernos:

```text
00_arranque → 01_exploracion → 02_baselines_B0_B1 → 03_baseline_B2 → 04_baseline_B3 → 05_baseline_B4 → 06_evaluacion_final
```

Celdas, tiempos y errores frecuentes: [`notebooks/EjecucionDeLosCuadernos.md`](notebooks/EjecucionDeLosCuadernos.md).

---

## 4. Sin acceso al dataset del equipo

El cuaderno `00_arranque` reconstruye las tablas desde el corpus público de Kaggle (días en `configs/dias.yaml`, unos 12 minutos por día). Para guardar los resultados, crea un dataset propio y pon su nombre en `configs/datos.yaml`. Después, los cuadernos 01 a 06 recalculan todo; los tiempos están en `EjecucionDeLosCuadernos.md`.

---

## 5. Pruebas

```bash
PYTHONPATH=src python -m pytest -q tests
```

Usan datos sintéticos y no descargan nada. Comprueban los invariantes de fuga, las particiones, la evaluación y el almacén de Kaggle. También corren dentro de los cuadernos 00 y 06. En Windows pueden fallar por bloqueo de archivos; la referencia es Linux.

---

## 6. Documentos relacionados

| Documento | Contenido |
|---|---|
| [`notebooks/EjecucionDeLosCuadernos.md`](notebooks/EjecucionDeLosCuadernos.md) | Qué hace cada cuaderno, orden de celdas, tiempos y cómo reproducir los resultados del artículo |
| [`docx/05AmbienteDeDesarrollo/DiccionarioDeDatos.md`](docx/05AmbienteDeDesarrollo/DiccionarioDeDatos.md) | Qué es cada fila y columna, particiones y reglas para modelar |
| [`docx/00ReglasGit/ReglasGit.md`](docx/00ReglasGit/ReglasGit.md) | Ramas, commits y PR |
| [`docx/04Herramientas/HerramientasDeDesarrollo.md`](docx/04Herramientas/HerramientasDeDesarrollo.md) | Herramientas, librerías y herramientas de IA |