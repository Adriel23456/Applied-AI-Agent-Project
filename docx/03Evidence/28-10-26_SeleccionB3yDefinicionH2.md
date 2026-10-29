# Selección global de B3 y definición operativa de H2

**Fecha:** 28 de octubre de 2026

**Propósito:** aclarar cómo se escoge una configuración común de B3 sin confundir
el criterio interno de selección con el reporte de A, B y C, y precisar qué se
compara en H2.

## Reporte de escenarios y selección global

Los escenarios A, B y C responden preguntas distintas: partidas nuevas, cambio
temporal y arquetipos reservados. Por ello, los resultados de desempeño se
presentan por escenario, sin mezclar las filas ni publicar un promedio como si
fuera una cuarta evaluación.

El objetivo para B3 es escoger **una configuración común** y usarla en los
tres escenarios. Para seleccionar entre configuraciones finalistas con los
mismos hiperparámetros evaluadas en A, B y C, se acordó usar el macro-promedio
simple del AUC global de `val`:

\[
\mathrm{macroAUC}(c) = \frac{\mathrm{AUC}_{A}(c) +
\mathrm{AUC}_{B}(c) + \mathrm{AUC}_{C}(c)}{3}.
\]

Cada escenario pesa lo mismo, independientemente del número de partidas de
`val`. El macro-AUC es exclusivamente una regla interna para escoger la
configuración; el informe conserva AUC, log loss y Brier por separado para A,
B y C. No se promedian log loss y Brier ni se mezclan métricas con pesos
arbitrarios. AUC se mantiene como métrica primaria.

Esta regla compara las finalistas existentes; no afirma que Optuna encontró el
óptimo global. Tampoco demuestra significancia estadística. No se requiere una
nueva búsqueda ni un bootstrap emparejado para aplicar la regla acordada.

## Aplicación a los CSV B3 disponibles

Entre las finalistas de CV con hiperparámetros idénticos en los tres
escenarios, el mayor macro-AUC observado corresponde al bosque aleatorio
seleccionado por log loss:

| Familia / finalista CV | AUC `val` A | AUC `val` B | AUC `val` C | Macro-AUC (solo selección) |
|---|---:|---:|---:|---:|
| Árbol / log loss | 0.7740 | 0.7343 | 0.7791 | 0.7624 |
| Árbol / Brier | 0.7767 | 0.7344 | 0.7810 | 0.7641 |
| Bosque / Brier | 0.8016 | 0.7621 | 0.8038 | 0.7892 |
| **Bosque / log loss** | **0.8029** | **0.7609** | **0.8063** | **0.7901** |

Hiperparámetros de la configuración seleccionada: `criterion=gini`,
`max_depth=12`, `min_samples_leaf=20`, `n_estimators=25`, `max_features=0.5`.
Los valores de validación subyacentes permanecen en
`results/baseline3/b3_val_A.csv`, `b3_val_B.csv` y `b3_val_C.csv`; el README de
esa carpeta conserva las métricas por escenario.

La finalista de log loss lidera las tres métricas en A y C. En B, la finalista
de Brier supera a la elegida en AUC y Brier; la finalista por AUC presenta un
log loss apenas menor que la de Brier. Esta diferencia por escenario queda
visible en el reporte y no se oculta con el macro-AUC.

La configuración elegida se ajusta por separado con el `train` propio de A, B
y C para medirla bajo cada partición. Esto no son tres selecciones de
hiperparámetros: es una misma configuración compartida con tres evaluaciones.
El artefacto que se use en la aplicación final se definirá según su escenario
de uso.

## Definición operativa de H2

La hipótesis H2 del artículo plantea que la señal temprana no se explica solo
por el turno y la identidad del mazo. Para que la comparación del Plan sea
reproducible, se distinguen estas entradas:

- **Estado completo:** 62 características públicas del tablero usadas por el
  modelo principal. Excluye los IDs de carta.
- **Versión restringida:** cuatro características: `game_turn`,
  `first_player_is_me`, `own_active_card` y `opp_active_card`.
- Los dos IDs son las identidades de los Pokémon activos visibles en ese
  estado. Son una aproximación a la identidad del mazo, no su composición
  completa.
- La opción `include_cards=True` da 64 características (estado completo más
  los dos IDs). Es una ablación diferente y no equivale a la versión
  restringida de cuatro entradas.

La interpretación de H2 debe mencionar la limitación del proxy de identidad:
el corpus no ofrece una característica de identidad completa del mazo que
pueda introducirse en cada estado sin usar metadatos agregados de toda la
partida. Los IDs de carta se mantienen fuera del modelo principal y solo se
usan en las comparaciones declaradas para H2.

## Documentos alineados

- `docx/05AmbienteDeDesarrollo/DiccionarioDeDatos.md`, sección 10: separa
  reporte por escenario de la selección global de B3 y define las entradas de
  H2.
- `docx/03Evidence/12-10-26_AcuerdosTecnicosModelado.md`: registra la regla
  como actualización metodológica posterior.
- `docx/01SeguimientoDeTareas/PlanDeDesarrollo.md`: explicita las cuatro
  características de la versión restringida.
- `docx/02Papers/00MainPaper/sec/04metodologia.tex`: refleja la regla de
  selección y la definición operativa de H2 en metodología.
- `results/baseline3/README.md`: presenta la decisión B3 y sus métricas
  individuales por escenario.
