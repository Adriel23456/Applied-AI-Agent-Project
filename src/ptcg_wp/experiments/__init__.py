"""Experimentos de la etapa 04 que acompanan a la escalera de baselines.

No buscan otro modelo principal: cada uno responde una pregunta del articulo usando solo
train y val (calib y test quedan reservados).

- leakage:        B2 con division por fila contra division por partida (fuga).
- lightgbm_vs_b4: verificacion de implementacion de B4 con LightGBM (regla de sustitucion).
- ablation:       B4 sin una familia de caracteristicas (aporte de cada familia).
- h2:             B4 restringido a turno, primer jugador e ids activos (hipotesis H2).
"""
