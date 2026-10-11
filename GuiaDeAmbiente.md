# Guía del ambiente de desarrollo — Etapa 2

Cómo preparar el ambiente, en qué orden ejecutar todo y para qué sirve cada cuaderno `.ipynb`.

---

## 1. La idea en una tabla

Tres piezas con trabajos distintos que nunca se mezclan:

| Pieza | Para qué sirve | Qué guarda | Qué se pierde |
|---|---|---|---|
| **Tu PC + VS Code** | Escribir código y hacer commits | Todo el repo | Nada |
| **GitHub** | Fuente de verdad del código | Código, cuadernos, configuraciones, documentos | Nada |
| **Servidor de Colab** | Prestar CPU y RAM para ejecutar | Nada permanente | **Todo** al desconectarse |

Flujo de trabajo:

```text
Editas en VS Code → commit y push → Colab clona desde GitHub → ejecuta → resultados en /content
```

Consecuencia: **antes de ejecutar en Colab, el código debe estar subido a GitHub**, porque Colab lo descarga de ahí. Lo que solo está en tu PC, Colab no lo ve.

Los commits se hacen siempre desde la PC, nunca desde Colab.

---

## 2. Preparación (una sola vez por persona)

1. **Cuenta de Kaggle y token.** kaggle.com → Settings → API → *Create New Token*. Cada integrante usa su propio token.
2. **Archivo `secrets.txt`** en tu PC, con el nombre del secreto y el valor en la línea siguiente:

   ```text
   KAGGLE_API_TOKEN
   <tu token>
   ```

   Está en el `.gitignore`. Nunca se sube al repo ni se pega en el chat o en un cuaderno.
3. **VS Code** con las extensiones de Jupyter y de Colab.
4. **Clonar el repo** y cambiarte a la rama de trabajo de la etapa.
5. **Colab Pro** en tu cuenta de Google.

---

## 3. Orden de ejecución en cada sesión

1. En tu PC, haz `git pull` en tu rama y confirma que lo que quieres probar ya está en GitHub (`git push`).
2. Abre `notebooks/00_arranque.ipynb` en VS Code.
3. Arriba a la derecha: *Select Kernel* → *Colab* → *New Colab Server*.
   - Elige **CPU** y, si aparece, **High-RAM**.
   - No uses GPU: toda la escalera de modelos es scikit-learn y no la aprovecha.
4. Ejecuta las celdas **en orden, de arriba abajo**:

| # | Celda | Qué hace | Resultado esperado |
|---|---|---|---|
| 1 | Clonar e instalar | Clona o actualiza el repo en `/content/repo`, instala `requirements.txt`, agrega `src/` al path | Sin errores |
| 2 | Kaggle | Obtiene el token (te lo pide arriba en VS Code) y lista datasets | 5 datasets listados |
| 3 | Ingesta | Descarga cada día de `configs/dias.yaml`, escribe un Parquet por día y borra el crudo | Una línea por día: `AAAA-MM-DD: N partidas -> ...parquet` |
| 4 | Verificación | Lee los Parquet y cuenta ganadores | Forma `(N, 10)` y recuento de `winner` |

5. Cuando termine, abre el cuaderno de tu rama (sección 5). Cada cuaderno lee lo que dejó el anterior en `/content/datos`.

**Si cierras o se desconecta el servidor:** `/content` queda vacío. Vuelve al paso 3. El código se vuelve a clonar solo y los datos se reconstruyen con la celda 3.

---

## 4. Qué sobrevive y qué no

| Qué | Dónde está | ¿Sobrevive a una desconexión? |
|---|---|---|
| Código y cuadernos | GitHub | Sí |
| Configuraciones (`dias.yaml`, semillas) | GitHub | Sí |
| Token de Kaggle | `secrets.txt` en tu PC | Sí, pero hay que dárselo de nuevo al servidor |
| Crudo de Kaggle | `/content/raw` | No (y se borra solo tras cada día) |
| Parquet procesados | `/content/datos` | **No** |
| Variables en memoria | RAM | No |

Los datos no viven en el repo. El repo guarda la receta (`ingest.py` + `dias.yaml`), que da el mismo resultado para todos.

---

## 5. La idea de los cuadernos

**Regla de oro:** el cuaderno cuenta la historia y muestra resultados; la lógica vive en `src/ptcg_wp/*.py`.

Así el código se puede importar desde el agente de la Etapa 3, probar con `pytest` y revisar en un PR sin pelear con el JSON del `.ipynb`.

Propuesta de cuadernos, uno por bloque de trabajo:

| Cuaderno | Qué hace | Lee | Escribe |
|---|---|---|---|
| `00_arranque` | Prepara el ambiente y reconstruye los datos | Kaggle | `/content/datos/partidas_*.parquet` |
| `01_exploracion` | EDA de la tabla, diccionario de datos, auditoría de fuga | Parquet | Figuras y tablas en `results/` |
| `02_baselines` | B0, B1 y B2 bajo el protocolo agrupado | Tabla de estados | Métricas en `results/` |
| `03_modelo_principal` | B3, B4 y búsqueda de hiperparámetros | Tabla de estados | Modelo exportado y métricas |
| `04_evaluacion_xai_calibracion` | Prueba única, SHAP y calibración | Modelo y tabla | Resultados finales |

Reglas:

- Cada cuaderno empieza con la misma celda corta de clonar e instalar, para poder abrirse solo.
- Lo exploratorio (inspeccionar un JSON, probar una idea) va en `01_exploracion`, no en `00_arranque`.
- `00_arranque` queda limpio: solo ambiente y datos.

---

## 6. Reglas de Git para los cuadernos

- **Limpiar las salidas antes de cada commit** (*Clear All Outputs* en la barra del cuaderno). Las salidas generan conflictos de merge y pueden filtrar información.
- Solo el cuaderno final entregable se sube **con** salidas, porque la rúbrica pide evidencia. Lo hace una sola persona.
- Dos personas no editan el mismo cuaderno a la vez.
- No se sube: tokens, `secrets.txt`, datos crudos, Parquet, modelos entrenados.

---

## 7. Cambiar los días de datos

Se edita `configs/dias.yaml`. Cada día cuesta unos 10 minutos de ingesta y 21 GB de disco temporal, y el disco se libera al terminar cada día.

Durante el desarrollo conviene dejar uno o dos días activos y comentar el resto:

```yaml
dias:
  - "2026-06-18"
#  - "2026-06-19"
```

La lista completa se activa una sola vez, para los resultados finales.

---

## 8. Notas del formato de los datos

Observadas en una partida de ejemplo; son la base de `features.py`.

- **Quién actúa en cada paso:** el jugador cuyo `status` es `ACTIVE`. El otro aparece como `INACTIVE` y su observación va un turno atrás.
- **`select` no distingue** al jugador que actúa: venía con contenido para ambos.
- **Información oculta:** la mano del oponente llega como `null` y los premios como una lista de `null`. Sus tamaños sí se ven.
- **Cartas:** se identifican por `id` numérico; el Pokémon en juego trae `hp`, `maxHp` y `energies`.
- **Premios restantes:** se cuentan con el **largo** de la lista `prize`, no contando elementos no nulos, porque todos son `null`.

---

## 9. Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `TimeoutException ... Secrets can only be fetched when running from the Colab UI` | `userdata` no funciona desde VS Code | `colab.py` ya cae a `secrets.txt` o a pedir el token a mano |
| `ModuleNotFoundError: ptcg_wp` | `src/` no está en el path | Ejecutar la celda 1; en la terminal, usar `PYTHONPATH=src` |
| `JSONDecodeError` al leer un día | Descarga incompleta | Volver a ejecutar la celda 3: sin el marcador `.completo`, la carpeta se borra y se descarga de nuevo |
| El repo en Colab no tiene mis cambios | No hiciste push | `git push` desde la PC y volver a ejecutar la celda 1 |
| Todo se perdió | El servidor se reinició | Normal: volver a la sección 3, paso 3 |