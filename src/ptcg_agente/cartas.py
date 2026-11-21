"""Catalogo de cartas para el simulador: cada carta que aparecio como Pokemon activo en el
entrenamiento (train de A) con sus PV maximos.

Las repeticiones no traen el nombre ni los PV de las cartas que no estan en juego, pero las
tablas de estados si guardan, para cada estado, la carta activa de cada jugador y sus PV
maximos. Con eso se arma el catalogo completo (la moda de los PV maximos de cada carta, porque
algunas herramientas los cambian). Lo construye la parte 4 del cuaderno 09 y se publica en
agente/cartas.json.
"""

import pandas as pd

RUTA = "agente/cartas.json"
COLUMNAS = ["own_active_card", "own_active_max_hp", "opp_active_card", "opp_active_max_hp"]
SIN_CARTA = -1


def construir(tabla):
    """tabla: filas de entrenamiento con COLUMNAS. Devuelve el diccionario que se guarda en JSON."""
    partes = [tabla[[f"{lado}_active_card", f"{lado}_active_max_hp"]].set_axis(["id", "maxHp"], axis=1)
              for lado in ("own", "opp")]
    t = pd.concat(partes, ignore_index=True)
    t = t[(t["id"] != SIN_CARTA) & (t["maxHp"] > 0)].astype({"id": int, "maxHp": int})
    grupos = t.groupby("id")["maxHp"]
    moda = grupos.agg(lambda s: int(s.value_counts().index[0]))
    veces = grupos.size()
    return {"fuente": "estados train del escenario A (carta activa de cada jugador)",
            "cartas": [{"id": int(c), "maxHp": int(moda[c]), "apariciones": int(veces[c])}
                       for c in moda.index]}