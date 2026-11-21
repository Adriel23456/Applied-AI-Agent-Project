"""Dominio de entrenamiento del modelo: perfil (se construye una vez) y revision de entradas.

El perfil se calcula SOLO con las filas train del escenario A, que es con lo que se entreno el
modelo final. Guarda, por caracteristica, el minimo, el maximo y los percentiles 0.5 y 99.5;
las cartas que aparecieron como Pokemon activo; y los cortes de etapa. Se publica en Kaggle
como agente/dominio.json desde el cuaderno 07_agente.

La revision compara una observacion con ese perfil y devuelve hallazgos con severidad:
  - "fuera": el valor nunca se vio en entrenamiento (fuera de [min, max]) o la carta es nueva.
  - "rara": el valor esta en la cola de la distribucion (fuera del 99 % central).
  - "nota": informacion util que no invalida la prediccion (por ejemplo, etapa de inicio).
"""

import numpy as np

from ptcg_wp.features import extract_features

CARTAS = ("own_active_card", "opp_active_card")
SIN_CARTA = -1


def construir_perfil(tabla, features, cortes, escenario="A"):
    """Perfil del dominio a partir de las filas train (DataFrame con features y cartas)."""
    rangos = {}
    for f in features:
        v = tabla[f].to_numpy(dtype=float)
        p005, p995 = np.quantile(v, [0.005, 0.995])
        rangos[f] = {"min": float(v.min()), "max": float(v.max()),
                     "p005": float(p005), "p995": float(p995)}
    cartas = set()
    for c in CARTAS:
        cartas.update(int(x) for x in tabla[c].unique() if int(x) != SIN_CARTA)
    return {"escenario": escenario, "n_filas": int(len(tabla)),
            "n_partidas": int(tabla["game_id"].nunique()) if "game_id" in tabla else None,
            "cortes_etapa": [float(cortes[0]), float(cortes[1])],
            "rangos": rangos, "cartas_activas": sorted(cartas)}


def etapa(turno, cortes):
    c1, c2 = cortes
    return "inicio" if turno <= c1 else ("medio" if turno <= c2 else "final")


def revisar(cur, perfil, features):
    """Hallazgos de una observacion ya validada frente al perfil. Lista de diccionarios."""
    return revisar_fila(extract_features(cur), perfil, features)


def revisar_fila(fila, perfil, features):
    """Lo mismo que revisar, con las caracteristicas ya calculadas (evita extraerlas dos veces)."""
    hallazgos = []
    for f in features:
        r = perfil["rangos"].get(f)
        if r is None:
            continue
        v = float(fila[f])
        if v < r["min"] or v > r["max"]:
            hallazgos.append({"severidad": "fuera", "tipo": "valor_no_visto", "caracteristica": f,
                              "valor": v, "rango_entrenamiento": [r["min"], r["max"]]})
        elif v < r["p005"] or v > r["p995"]:
            hallazgos.append({"severidad": "rara", "tipo": "valor_poco_frecuente",
                              "caracteristica": f, "valor": v,
                              "rango_habitual": [r["p005"], r["p995"]]})
    vistas = set(perfil["cartas_activas"])
    for c in CARTAS:
        carta = int(fila[c])
        if carta != SIN_CARTA and carta not in vistas:
            hallazgos.append({"severidad": "fuera", "tipo": "carta_no_vista", "caracteristica": c,
                              "valor": carta})
    return hallazgos