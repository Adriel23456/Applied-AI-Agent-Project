"""Agente multiagente que consume el modelo final de probabilidad de victoria (Etapa 3).

Mapa del paquete, en el orden en que se recomienda leerlo:

  artefactos.py      Baja de Kaggle el modelo final y sus archivos de apoyo, y los verifica
                     (SHA-256 contra el indice del dataset y version de scikit-learn).
  modelo.py          Carga todo una sola vez: predictor, explicador SHAP, ficha, metricas
                     de test y perfil de dominio.
  entradas.py        Convierte lo que llega (observacion, archivo de observacion o repeticion
                     completa) en la observacion del jugador que actua.
  dominio.py         Perfil del dominio de entrenamiento y deteccion de entradas fuera de el.
  lenguaje.py        Nombres en espanol de las caracteristicas y sus familias.
  registro.py        Registro JSONL de cada invocacion (evidencia de la integracion).
  herramientas/      Una herramienta por archivo. No dependen de ningun LLM.
  agentes/           Roles de la arquitectura multiagente (verificador, planificador,
                     ejecutor y redactor).
  servidor_mcp.py    Expone las herramientas a Claude Desktop y Claude Code (protocolo MCP).

El modelo no se reentrena ni se recalibra aqui: se usa tal como quedo en la Etapa 2.
"""