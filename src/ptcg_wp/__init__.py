"""Paquete del proyecto: probabilidad de victoria desde el estado de juego en Pokemon TCG."""

import warnings

# Optuna marca como "experimentales" dos argumentos que el proyecto usa a proposito:
# multivariate=True en TPESampler (b3.py y b4.py) y heartbeat_interval en RDBStorage
# (checkpoints.py). Funcionan bien y estan fijados con optuna==4.6.0; el aviso solo
# advierte que su interfaz podria cambiar en otra version. Se silencia SOLO ese aviso.
warnings.filterwarnings(
    "ignore",
    message=r"Argument ``(multivariate|heartbeat_interval)`` is an experimental feature",
)