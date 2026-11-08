"""Simulador grafico del agente (rama 08AgentValidationAndSimulator).

Aplicacion web local, sin dependencias nuevas (servidor HTTP de la biblioteca estandar y una
pagina HTML con JavaScript):
  servidor.py     API local: evaluar un estado, cargar una partida y moverse paso a paso.
  web/index.html  Interfaz: tablero de ambos jugadores editable, probabilidad en tiempo real,
                  contribuciones SHAP, advertencias del verificador y curva de la partida.

Uso desde la raiz del repositorio (con .venv activo):
    python -m ptcg_agente.simulador --archivo artefactos_agente/agente/ejemplos/partida_XXXX.json
Desde Claude (servidor MCP): herramienta abrir_simulador.
"""