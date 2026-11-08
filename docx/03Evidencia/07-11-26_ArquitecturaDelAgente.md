# Arquitectura del agente (Etapa 3)

Rama: `07MultiAgentIntegration`. Documento escrito antes de integrar el agente con Claude; fija los roles, las herramientas, el flujo de una consulta, el registro y cómo se verifica cada respuesta.

## 1. Qué hace el agente

Responde preguntas sobre partidas del Pokémon TCG usando el modelo final de la Etapa 2: quién va ganando, por qué, cómo cambió la probabilidad a lo largo de una partida y qué estado alternativo favorece más al jugador que actúa. El modelo es B4 entrenado en el escenario A, sin recalibrar, y se consume tal como se evaluó.

El agente nunca recibe ni pide información oculta (mano del rival, contenido de los premios). Usa solo la observación pública del jugador que actúa, igual que el modelo.

## 2. Decisión del LLM

**Decisión:** el agente se usa desde **Claude Desktop** o **Claude Code**, con la membresía del equipo, a través de un servidor MCP propio. No se usa una clave de API.

**Por qué:** el equipo ya tiene la membresía, así que no hay costo adicional, y MCP es el protocolo que ambos clientes usan para invocar herramientas externas. Las herramientas y el verificador no dependen del LLM, así que se prueban con `pytest` sin Claude.

**Descartado:**
- API de Claude con clave propia: costo por uso y una credencial más que proteger.
- Un LLM simulado para pruebas: las partes deterministas (herramientas, verificador, servidor) se prueban directamente, y el comportamiento del LLM se valida con sesiones reales registradas.

## 3. Roles

| Rol | Quién lo cumple | Qué hace |
|---|---|---|
| **Planificador** | Claude | Interpreta la consulta y decide qué herramientas llamar y en qué orden |
| **Ejecutor** | Servidor MCP (`ptcg_agente.herramientas`) | Valida la entrada, corre el modelo y devuelve resultados estructurados |
| **Verificador** | Servidor MCP (`ptcg_agente.agentes.verificador`), determinista | Revisa cada resultado antes de devolverlo y revisa el borrador final con `verificar_respuesta` |
| **Redactor** | Claude | Escribe la respuesta para un usuario no técnico: probabilidad, explicación y límites |

El verificador es código, no un LLM: sus decisiones son reproducibles y tienen pruebas automáticas. Un agente que confía ciegamente en el modelo sería frágil; aquí ninguna cifra llega al usuario sin pasar por el verificador.

## 4. Herramientas

| Herramienta | Entrada | Salida |
|---|---|---|
| `estimar_probabilidad` | Observación, archivo de observación o repetición + `paso` | Probabilidad de victoria del jugador que actúa, etapa, AUC de prueba de esa etapa, revisión de dominio y advertencias |
| `explicar_prediccion` | Igual que la anterior + `top` | Contribuciones SHAP a favor y en contra (en log-odds y en puntos porcentuales), resumen por familia y texto en lenguaje natural |
| `evaluar_partida` | Repetición completa | Probabilidad del jugador 0 por paso y por turno, puntos de giro y ganador real |
| `comparar_estados` | 2 a 8 estados del mismo jugador | Probabilidad de cada uno, diferencia contra el primero y el mejor |
| `revisar_dominio` | Igual que `estimar_probabilidad` | Si el modelo aplica y si la entrada está dentro del dominio de entrenamiento |
| `describir_modelo` | Nada | Ficha del modelo, métricas de prueba por escenario y etapa, veredicto de H1 a H3 y límites |
| `verificar_respuesta` | Borrador del texto final | Si el texto es coherente con los resultados de la sesión |

Cada herramienta está en su propio archivo de `src/ptcg_agente/herramientas/`.

## 5. Flujo de una consulta

```text
Usuario ──► Claude (planificador)
              │ decide herramientas
              ▼
          Servidor MCP (ejecutor) ──► modelo final ──► resultado
              │                                         │
              │                    verificador: verificar_salida
              ▼                                         │
          Claude (redactor) ◄──── resultado + "verificacion"
              │ borrador
              ▼
          verificar_respuesta (verificador) ── no aprueba ──► Claude corrige
              │ aprueba
              ▼
          Respuesta al usuario
```

Las instrucciones del servidor MCP le piden a Claude seguir estos cuatro pasos en cada consulta.

## 6. Qué comprueba el verificador

**Sobre cada resultado de herramienta** (`verificar_salida`):
- Toda probabilidad está en [0, 1]. Es `None` solo cuando el modelo no aplica (preparación o estado resuelto).
- En las explicaciones, valor base + suma de SHAP = logit del modelo (tolerancia 1e-3), y sigmoide(logit) = probabilidad.
- Están las advertencias obligatorias: `etapa_inicio` al inicio de la partida, `fuera_de_dominio` si hay valores o cartas nunca vistos y `sin_prediccion` si el modelo no aplica.

**Sobre la respuesta final** (`verificar_texto`):
- Toda cifra del texto sale de alguna herramienta, con tolerancia de redondeo. Los conteos pequeños sin porcentaje ("dos premios") se permiten.
- Si hubo advertencias, el texto las menciona.
- Si el modelo no aplica, el texto lo dice y no da porcentajes.
- El texto no promete certeza ("garantiza", "con certeza", "sin duda").

## 7. Advertencias

| Código | Cuándo | Por qué |
|---|---|---|
| `sin_prediccion` | Turno 0 o estado ya resuelto | El modelo no se entrenó con esos estados |
| `etapa_inicio` | Turno ≤ 5 | AUC de prueba 0.684 en A: el modelo distingue poco |
| `extrema_temprana` | Probabilidad ≥ 0.9 o ≤ 0.1 al inicio | Ahí las predicciones muy seguras fallan con más frecuencia |
| `fuera_de_dominio` | Valor fuera del rango de entrenamiento o carta activa nunca vista | La probabilidad puede no ser confiable |
| `poco_frecuente` | Valor fuera del 99 % central del entrenamiento | Aviso leve |

El perfil del dominio (`agente/dominio.json`) se calcula solo con las filas `train` del escenario A.

## 8. Registro de invocaciones

Cada llamada queda en `registros/agente_AAAA-MM-DD.jsonl`, una línea por invocación:

```json
{"fecha_utc": "...", "sesion": "9c705796203c", "agente": "ejecutor",
 "herramienta": "estimar_probabilidad", "entrada": {"archivo": "partida_123.json", "paso": 40},
 "salida": {"ok": true, "probabilidad": 0.63, "verificacion": {"aprobado": true}},
 "duracion_ms": 41.2, "modelo_sha256": "...", "commit": "d12d693"}
```

Las observaciones grandes se guardan como su hash, no completas. Las sesiones que sirven de evidencia se copian a `docx/03Evidencia/`.

## 9. Integridad del modelo

Al arrancar, el agente verifica:
1. Cada archivo (modelo, ficha, dominio, métricas, veredicto) tiene el SHA-256 que registra el índice del dataset de Kaggle.
2. La versión de scikit-learn instalada es la misma con que se guardó el modelo.

Si algo no coincide, el servidor no responde con el modelo y explica el motivo.

## 10. Archivos

| Archivo | Contenido |
|---|---|
| `src/ptcg_agente/artefactos.py` | Descarga y verificación de los archivos del agente |
| `src/ptcg_agente/modelo.py` | Carga única del modelo, SHAP, ficha, métricas y perfil |
| `src/ptcg_agente/entradas.py` | Validación de observaciones, archivos y repeticiones |
| `src/ptcg_agente/dominio.py` | Perfil del dominio y revisión de entradas |
| `src/ptcg_agente/lenguaje.py` | Nombres en español de las características |
| `src/ptcg_agente/registro.py` | Registro JSONL |
| `src/ptcg_agente/herramientas/` | Una herramienta por archivo |
| `src/ptcg_agente/agentes/verificador.py` | Verificador |
| `src/ptcg_agente/servidor_mcp.py` | Servidor MCP |
| `src/ptcg_agente/ejemplos.py` | Repeticiones reales de ejemplo |
| `.mcp.json` | Registro del servidor para Claude Code |
| `notebooks/07_agente.ipynb` | Perfil del dominio, ejemplos y verificación con partidas reales |
| `tests/test_agente.py` | Pruebas del agente |

Instalación y uso: `docx/05AmbienteDeDesarrollo/GuiaDelAgente.md`.
