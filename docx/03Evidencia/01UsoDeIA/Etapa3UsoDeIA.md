# Declaración de Uso de Herramientas de IA

**Proyecto:** Estimación de la Probabilidad de Victoria a partir del Estado de Juego en el Pokémon Trading Card Game: un Estudio de Clasificación Tabular con Control Explícito de Fuga de Información

**Curso:** IC-6200 — Inteligencia Artificial, ITCR · II Semestre 2026 · Track A

**Equipo:** Adriel S. Chaves Salazar · Daniel Duarte Cordero · Sebastián Hernández Bonilla

**Cubre:** Etapa 3 — Agente, validación, ética y artículo final (ramas `07MultiAgentIntegration`, `08AgentValidationAndSimulator`, `09EthicsPaperAndDocumentation` y `10DefenseAndShowcase`)

**Estado:** completa hasta la rama 09. Cada integrante revisa su bloque de la sección 5 antes de la entrega.

Esta declaración se suma a `Etapa1UsoDeIA.md` y `Etapa2UsoDeIA.md`, no las sustituye.

---

## 1. Dos usos distintos de la IA en esta etapa

En la Etapa 3 la IA aparece de dos formas, y conviene no confundirlas:

| Uso | Qué es | Dónde se declara |
|---|---|---|
| **La IA como herramienta de trabajo** | El equipo usó Claude para programar, revisar, diagnosticar errores y redactar, igual que en las etapas anteriores | Esta declaración |
| **La IA como parte del sistema** | El agente del proyecto usa Claude como planificador y redactor (`claude -p`), y Claude Code o Claude Desktop como interfaz con el servidor MCP | `docx/03Evidencia/07-11-26_ArquitecturaDelAgente.md` y la sección "Integración y Validación del Agente" del artículo |

El segundo uso es el objeto de estudio: sus respuestas se validaron con un protocolo escrito antes de ejecutar (`08-11-26_ProtocoloValidacionAgente.md`). Esta declaración trata solo del primero.

---

## 2. Herramientas utilizadas

| Herramienta | Quién | Propósito en esta etapa |
| --- | --- | --- |
| **Claude (Anthropic), modelo Opus 5.5, en la aplicación de Claude con ejecución de código** | Adriel | Ramas 07, 08 y 09: diseño e implementación del agente, del servidor MCP, del orquestador, de la batería de validación y del simulador; diagnóstico de errores; borradores de la documentación, de la ética y de las secciones nuevas del artículo. |
| **Claude (Anthropic)** | Daniel | Revisión del proceso y del funcionamiento de lo desarrollado en la etapa, según su propia evaluación humana, y apoyo en las evaluaciones (validación humana con el simulador y revisión de resultados). |
| **Claude (Anthropic)** | Sebastián | Revisión del proceso y del funcionamiento de lo desarrollado en la etapa, según su propia evaluación humana, y apoyo en las evaluaciones (validación humana con el simulador y revisión de resultados). |

Ninguna herramienta tuvo acceso al dataset privado de Kaggle ni al token. Todas las cifras de la etapa salen de celdas o comandos ejecutados por el equipo y quedan trazadas en Kaggle (`adrielchavessalazar/ptcg-wp-tablas`, carpeta `agente/`) o en los archivos de `docx/03Evidencia/`.

---

## 3. Dónde se usó la IA y qué se hizo manualmente después

### 3.1 Rama `07MultiAgentIntegration` (Adriel, con Claude)

**Qué hizo la herramienta.** A partir de las indicaciones de Adriel, propuso la arquitectura (`07-11-26_ArquitecturaDelAgente.md`) e implementó:

- `src/ptcg_agente/herramientas/`: las seis herramientas del modelo (estimar, explicar, evaluar partida, comparar estados, revisar dominio y describir el modelo), cada una en su archivo;
- `artefactos.py` y `modelo.py`: descarga del modelo final desde Kaggle con verificación de SHA-256 y de la versión de scikit-learn;
- `agentes/`: planificador y redactor como llamadas separadas a Claude sin herramientas, ejecutor como código y verificador determinista;
- `registro.py`, `servidor_mcp.py`, `orquestador.py`, los subagentes de `.claude/agents/` y el comando `/consulta-ptcg`;
- las pruebas de `tests/test_agente.py` y los cuadernos `07_agente` y `08_agente_orquestador`.

**Verificado manualmente.** Adriel ejecutó el cuaderno 07 en Colab: 642 estados de 4 partidas reales con diferencia 0.0 frente al modelo final. Instaló el agente en su PC, aprobó el servidor en Claude Code y revisó la sesión guardada como evidencia, en la que el verificador rechazó un primer borrador.

**No generado por IA.** La decisión de usar la membresía de Claude sin clave de API, la ejecución de los cuadernos, la revisión de cada respuesta del agente que se guardó como evidencia y la aprobación de los commits.

### 3.2 Rama `08AgentValidationAndSimulator` (Adriel, con Claude; validación humana de los tres)

**Qué hizo la herramienta.** Redactó el borrador del protocolo de validación antes de ejecutarlo, implementó la batería N1 (`src/ptcg_agente/validacion/`), los cuadernos `09_validacion_agente` y `10_validacion_llm`, el simulador gráfico (`src/ptcg_agente/simulador/`) y la herramienta `abrir_simulador`. Diagnosticó, a partir de las salidas que Adriel copiaba, los errores de la ejecución:

- el límite 429 de Kaggle con descargas en paralelo;
- Kaggle no entregaba el archivo `.gz`;
- el error 400 al crear versiones con la herramienta `kaggle` 2.0.2;
- la lentitud de `evaluar_partida` (L-09, de 56.6 s a 0.9 s) y el caso sin Pokémon activo (L-10).

Rediseñó el simulador según las observaciones de Adriel: jugadores fijos, cifra siempre del jugador 0, estado nuevo vacío y PV de todas las cartas.

**Verificado manualmente.** Adriel ejecutó N1 en Colab y N2 en su PC (31 consultas). Revisó a mano las respuestas Q-01, Q-02 y Q-07. Rechazó la primera versión de la validación humana, que repetía las mismas pruebas para los tres integrantes, y pidió 5 pruebas distintas por persona. Cada integrante hizo sus 5 pruebas en su propia computadora (`08-11-26_ValidacionHumanaSimulador.md`).

**No generado por IA.** Las ejecuciones y sus cifras, las 15 pruebas con el simulador y sus porcentajes, el juicio de si cada dirección tenía sentido de juego y la aprobación de los commits y del PR #14.

### 3.3 Rama `09EthicsPaperAndDocumentation` (Adriel, con Claude)

**Qué hizo la herramienta.** Redactó los borradores de:

- `08-11-26_EticaDelDespliegue.md`: riesgos, datos sensibles, mitigaciones con su archivo y su prueba, límites y uso aceptable;
- las secciones nuevas del artículo (`sec/10agente.tex` y `sec/06etica.tex`) y los cambios del resumen, la introducción, la discusión y las conclusiones;
- la documentación del repositorio y la bitácora de la Etapa 3.

Todas las cifras se copiaron de los archivos de evidencia; la herramienta no calculó ninguna.

**Verificado manualmente.** Adriel comprobó que cada mitigación citada tuviera su archivo y su prueba, que cada cifra del artículo coincidiera con la evidencia y que el artículo compilara sin errores.

**No generado por IA.** La elección de los riesgos que importan para este sistema, la decisión de no ofrecer un servicio público y la aprobación final del texto.

### 3.4 Revisión del proceso y del funcionamiento (Daniel y Sebastián, con Claude)

**Qué hicieron.** Daniel y Sebastián usaron Claude para revisar y asegurar que el desarrollo de esta última etapa siguiera un proceso adecuado y que todo funcionara bien, según su propia evaluación humana. Además, ayudaron a Adriel con las evaluaciones descritas en 3.2. Concretamente:

- revisaron, con apoyo de Claude, si el trabajo de cada rama cumplía el plan de desarrollo, las reglas de la etapa (sin información oculta, sin reentrenar el modelo, protocolo escrito antes de ejecutar, ninguna credencial en el repositorio) y la rúbrica;
- instalaron el proyecto en sus computadoras y comprobaron que el agente y el simulador funcionaran en ellas;
- hicieron sus 5 pruebas de la validación humana con el simulador y anotaron la probabilidad que mostró;
- revisaron los resultados y la documentación, y comunicaron sus observaciones al equipo.

**Verificado manualmente.** La decisión de si algo funcionaba o estaba completo fue de ellos, no de la herramienta: probaron cada pieza en su propia computadora y contrastaron las salidas con lo que dicen los documentos.

**No generado por IA.** Los resultados de sus pruebas, su juicio sobre el funcionamiento y el proceso, y sus observaciones al equipo.

---

## 4. Límites establecidos por el equipo

Se mantienen los límites de las Etapas 1 y 2. En esta etapa se suman:

* **El agente no inventa cifras.** Toda probabilidad que el agente muestra sale de una herramienta y queda en el registro de invocaciones; el verificador rechaza las respuestas con cifras que no salieron de una herramienta.
* **La IA del agente no ve información oculta.** Ni el planificador ni el redactor reciben la mano del rival ni el contenido de los premios, y el planificador nunca ve el contenido del archivo de la partida.
* **El modelo no se reentrena.** El agente usa el modelo final de la Etapa 2, verificado por SHA-256.
* **Las claves de API se tratan como el token de Kaggle.** El agente usa la membresía por medio de Claude Code; no hay claves en cuadernos, archivos versionados ni conversaciones.
* **El protocolo de validación se escribió antes de ejecutar.** Los criterios de aprobación no se cambiaron al ver los resultados; las correcciones posteriores se reportan junto a la corrida original.
* **La evaluación humana no se delega.** Las pruebas con el simulador y el juicio de si una dirección tiene sentido de juego son de cada integrante.

---

## 5. Declaración por integrante

Cada miembro revisa su propio bloque antes de la entrega.

### Adriel S. Chaves Salazar

* **Herramientas utilizadas:** Claude (Anthropic), modelo Opus 5.5, en la aplicación de Claude con ejecución de código.
* **Dónde y para qué:** Ramas 07, 08 y 09 (secciones 3.1 a 3.3). Usé la herramienta como asistente de programación, de diagnóstico y de redacción: le describía el objetivo y las reglas del equipo, ejecutaba sus propuestas en Colab o en mi PC y le devolvía las salidas y los errores.
* **Verificado manualmente después:** Ejecuté los cuadernos 07 a 10, revisé las respuestas del agente guardadas como evidencia, hice mis 5 pruebas con el simulador, revisé Q-01, Q-02 y Q-07 y comprobé cada cifra del artículo contra los archivos de evidencia. Rechacé o corregí las propuestas que no cumplían lo pedido, por ejemplo un simulador cuya cifra cambiaba de jugador al avanzar la partida o una validación humana con pruebas repetidas.
* **No generado por IA:** Las ejecuciones y sus cifras, mis pruebas con el simulador, las decisiones de diseño (membresía sin clave de API, Kaggle como almacén único, sin servicio público) y la aprobación de los commits y PR.

### Daniel Duarte Cordero

* **Herramientas utilizadas:** Claude (Anthropic).
* **Dónde y para qué:** Revisión del proceso y del funcionamiento de la Etapa 3 y apoyo en las evaluaciones (sección 3.4). Usé la herramienta para revisar que el desarrollo siguiera el plan y las reglas del equipo, y para entender y comprobar el funcionamiento del agente y del simulador.
* **Verificado manualmente después:** Instalé el proyecto en mi computadora, comprobé que el simulador funcionara e hice mis 5 pruebas (D1 a D5). Evalué por mi cuenta si lo desarrollado funcionaba como dicen los documentos.
* **No generado por IA:** Los resultados de mis pruebas, mi evaluación del funcionamiento y del proceso y mis observaciones al equipo.

### Sebastián Hernández Bonilla

* **Herramientas utilizadas:** Claude (Anthropic).
* **Dónde y para qué:** Revisión del proceso y del funcionamiento de la Etapa 3 y apoyo en las evaluaciones (sección 3.4). Usé la herramienta para revisar que el desarrollo siguiera el plan y las reglas del equipo, y para entender y comprobar el funcionamiento del agente y del simulador.
* **Verificado manualmente después:** Instalé el proyecto en mi computadora, comprobé que el simulador funcionara e hice mis 5 pruebas (S1 a S5), incluida la del estado nuevo armado desde cero. Evalué por mi cuenta si lo desarrollado funcionaba como dicen los documentos.
* **No generado por IA:** Los resultados de mis pruebas, mi evaluación del funcionamiento y del proceso y mis observaciones al equipo.