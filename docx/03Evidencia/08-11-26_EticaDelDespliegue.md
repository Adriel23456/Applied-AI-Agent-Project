# Ética del despliegue (Etapa 3)

Rama: `09EthicsPaperAndDocumentation`. Este documento responde qué puede salir mal cuando alguien **usa** el sistema (el agente, el servidor MCP y el simulador), qué datos toca, qué se hizo para reducir cada riesgo y qué límites quedan. Cada mitigación apunta al código o a la prueba donde se puede comprobar. Las cifras salen de la validación de la rama 08 (`08-11-26_ResultadosValidacionAgente.md` y `08-11-26_ValidacionHumanaSimulador.md`).

## 1. Qué se despliega

| Pieza | Qué hace | Dónde corre |
|---|---|---|
| Modelo final (B4 entrenado en A) | Estima la probabilidad de que gane el jugador que actúa, a partir del estado público de la partida | En la computadora de quien lo usa |
| Agente (planificador, ejecutor, verificador y redactor) | Responde preguntas sobre una partida usando el modelo | Computadora local; Claude responde desde los servidores de Anthropic |
| Servidor MCP `ptcg-victoria` | Da las herramientas del modelo a Claude Desktop y Claude Code | Computadora local |
| Simulador | Página web para armar o recorrer un estado y ver la probabilidad | Computadora local (`127.0.0.1`, no es accesible desde otras computadoras) |

No hay un servicio público: cada persona instala el sistema en su computadora y lo usa con su propia cuenta de Claude.

## 2. Riesgos concretos del despliegue

Gravedad: qué tan malo sería si pasa. Probabilidad: qué tan fácil es que pase con el sistema tal como está.

| # | Riesgo | Qué podría pasar | Gravedad | Probabilidad |
|---|---|---|---|---|
| R1 | **Confianza excesiva en la probabilidad** | Un usuario toma un 90 % como certeza y decide mal. La validación midió que 50 de 60 errores muy seguros de medio y final llegan sin advertencia, y que el agente los presenta como fiables ("en la etapa final es donde mejor acierta") | Media | Alta |
| R2 | **Ventaja indebida en competencias** | Alguien consulta el agente o el simulador durante una partida en curso de un torneo, contra personas o contra otros agentes, donde las reglas prohíben ayuda externa | Media | Media |
| R3 | **Sesgo hacia el meta de agentes automáticos** | El modelo aprendió cómo juegan los agentes de una competencia durante diez días de 2026. Aplicado a personas, a otros mazos o a otra época, valora mal posiciones que ellos juegan distinto | Media | Alta si se usa fuera del corpus |
| R4 | **Mal uso en apuestas** | Alguien usa la probabilidad para apostar dinero sobre partidas | Alta | Baja |
| R5 | **Leer SHAP como causa** | El usuario cree que "agregar energías al activo hace perder", cuando es solo una asociación del modelo (validación humana, prueba D4) | Baja | Media |
| R6 | **Condiciones especiales ignoradas** | Quemado, dormido y paralizado no movieron la probabilidad en el estado probado (pruebas A4, D5 y S4), aunque en el juego sí importan | Baja | Alta |
| R7 | **Mezclar análisis posterior con predicción** | Con una repetición completa, el agente puede mencionar el ganador real (consultas Q-03 y Q-05). Es correcto para analizar una partida terminada, pero no es una predicción | Baja | Media |
| R8 | **Datos enviados a Claude** | Las preguntas del usuario y los resultados de las herramientas viajan a los servidores de Anthropic para que Claude responda | Baja | Segura (es como funciona) |

## 3. Datos sensibles involucrados

| Dato | Qué es | Cómo se trata |
|---|---|---|
| Nombres de los agentes del corpus | Seudónimos que eligieron los autores de los agentes de la competencia | Nunca se escriben en las tablas: se cambian por un código estable (`ptcg_wp.ingest.pseudonym`, SHA-256 truncado). No entran al modelo ni se publican comparaciones entre competidores |
| Licencia del corpus | Repeticiones públicas de Kaggle bajo CC0 (dominio público) | Se pueden usar y redistribuir; el dataset del equipo (`adrielchavessalazar/ptcg-wp-tablas`) es privado de todas formas |
| Información oculta del juego | La mano del rival y el contenido de los premios | El modelo y el agente nunca la usan. El extractor solo toma **cuántas** cartas hay en la mano y en los premios (`features.py`: `handCount`, largo de `prize`) |
| Registros de uso | Cada llamada a una herramienta: fecha, agente, entrada resumida, salida, duración, SHA-256 del modelo y commit | Se guardan solo en la computadora del usuario (`registros/`, fuera de Git). Las observaciones grandes se guardan como su hash, no completas |
| Credenciales | Token de Kaggle y sesión de Claude | Nunca en cuadernos, archivos versionados ni conversaciones. `secrets.txt` está en `.gitignore`; el token se pide sin mostrarlo |

No hay datos personales de jugadores humanos en ninguna parte del sistema: el corpus son partidas entre programas.

## 4. Mitigaciones aplicadas y cómo comprobarlas

| Mitigación | Riesgo que reduce | Dónde está | Cómo se comprueba |
|---|---|---|---|
| **Verificador determinista**: toda cifra de la respuesta debe salir de una herramienta; rechaza promesas de certeza y porcentajes cuando el modelo no aplica | R1 | `src/ptcg_agente/agentes/verificador.py` | `tests/test_agente.py`; en N2 rechazó 3 borradores y aprobó 31 de 31 respuestas finales |
| **Advertencias obligatorias**: confianza baja al inicio, probabilidad extrema temprana, fuera del dominio, valores poco frecuentes y "sin predicción" | R1, R3, R6 | `src/ptcg_agente/herramientas/comun.py` | Casos N-03, L-01 a L-08, E-07, E-08, S-01 a S-05 y M-01: 13 de 13 con la advertencia correcta |
| **Revisión de dominio**: compara cada estado con los rangos y cartas del entrenamiento | R3 | `src/ptcg_agente/dominio.py`, `agente/dominio.json` | Estados sintéticos S-01 a S-05: `fuera_de_dominio` en 100 de 100 |
| **Sin información oculta**: el modelo solo ve cantidades; el agente se niega a dar la mano rival o los premios | R2 | `src/ptcg_wp/features.py`; instrucciones del redactor y del servidor MCP | `tests/test_fuga.py::test_hidden_information_does_not_change_features`; consultas Q-01 y Q-02 (revisión humana: se niegan bien) |
| **Defensa ante instrucciones inyectadas**: el planificador y el redactor nunca ven el contenido del archivo, solo los resultados de las herramientas | R1 | `src/ptcg_agente/orquestador.py`, `agentes/planificador.py` | Consulta Q-05: el texto inyectado no llegó a ninguna herramienta ni a la respuesta |
| **Plan validado**: el planificador solo puede usar herramientas del catálogo | R1 | `agentes/planificador.py` (`validar`) | Consulta Q-06 y pruebas del planificador |
| **Lenguaje de estimación**: el redactor explica con premios, descartes, mazo y tablero, dice "estimación" y no promete certeza; el simulador dice que SHAP son asociaciones, no causas | R1, R5 | `agentes/redactor.py`, `simulador/web/index.html` | Consultas M-03 y Q-03; texto del panel SHAP |
| **Límites en la ficha del modelo**: `describir_modelo` devuelve las métricas por etapa y escenario y los límites declarados | R1, R3 | `herramientas/describir_modelo.py` | Consultas A-03 y Q-07 |
| **Integridad del modelo**: el agente solo arranca si el modelo y sus archivos coinciden por SHA-256 con los publicados | Uso de un modelo distinto al evaluado | `src/ptcg_agente/artefactos.py` | `tests/test_agente.py` (archivo alterado y otra versión de scikit-learn) |
| **Registros de cada invocación**: quién llamó a qué, con qué modelo y commit | Auditoría de cualquier riesgo | `src/ptcg_agente/registro.py` | Evidencia en `docx/03Evidencia/*.jsonl` |
| **Solo local**: el simulador escucha en `127.0.0.1` y no hay servicio público | R2, R4 | `simulador/servidor.py` | Dirección fija en el código |

## 5. Límites declarados del sistema

1. **Población:** partidas entre agentes automáticos de una competencia, en diez días de 2026. No representa el juego entre personas, ni otros mazos, ni otras épocas.
2. **Confianza por etapa:** al inicio de la partida el modelo distingue poco (AUC 0.683 en prueba); al final distingue bien (0.936). Ninguna etapa da certeza.
3. **Errores seguros invisibles:** en medio y final, la mayoría de los errores muy seguros llegan sin advertencia. En la etapa final, de cada 100 predicciones muy seguras (90 % o más, o 10 % o menos) fallan entre 2 y 4, y el sistema no sabe cuáles.
4. **Fuera de su población:** con días posteriores o mazos nuevos, el modelo pierde capacidad (AUC de 0.789 y 0.787) y tiende a confiar de más.
5. **Estados sin predicción:** la preparación (turno 0) y las partidas ya resueltas no tienen probabilidad.
6. **Condiciones especiales:** el modelo casi no usa quemado, dormido y paralizado, por lo poco que aparecen en el entrenamiento.
7. **Asociaciones, no causas:** las explicaciones SHAP dicen qué valores acompañan a ganar o perder, no qué los provoca.
8. **No recomienda jugadas:** estima quién va ganando; no dice qué hacer.
9. **Información oculta:** nunca usa la mano del rival ni el contenido de los premios. Por eso no puede responder preguntas sobre ellos.

## 6. Uso aceptable

- **Sí:** analizar partidas terminadas, aprender qué recursos pesan en una posición, explorar estados hipotéticos en el simulador, investigar el comportamiento del modelo.
- **No:** consultarlo durante una partida en curso donde las reglas prohíban ayuda externa, apostar dinero con sus cifras, usarlo para juzgar a jugadores humanos o tratar sus probabilidades como certezas.

## 7. Mejora propuesta (no aplicada)

Para R1, la validación propone que, en medio y final, el agente diga junto a una probabilidad muy segura cuántas veces fallan esas predicciones según la evaluación de la Etapa 2 (por ejemplo, "las predicciones de 90 % o más aciertan entre 96 y 98 de cada 100 al final"), en lugar de citar solo el AUC promedio. No se aplicó porque cambia el mensaje del agente después de su validación, y habría que volver a validarlo; queda como trabajo futuro.
