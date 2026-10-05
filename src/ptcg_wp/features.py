"""Extraccion de caracteristicas: convierte cada partida JSON en filas de estado.

Una fila = el estado del tablero visto por el jugador que actua en un paso.
La etiqueta y es 1 si ese jugador termina ganando la partida.
Solo se usa informacion publica del tablero: nunca la mano del oponente,
ni el contenido de los premios, ni resultados de la partida como caracteristicas.
"""

# Valor que se pone cuando algo no existe (por ejemplo, no hay Pokemon activo).
# Se usa junto con una columna indicadora (active_present) y no se imputa.
SENTINEL = -1

# Columnas que describen la fila pero NO deben entrar al modelo como caracteristicas
META_COLUMNS = ["game_id", "day", "step", "turn", "acting_index", "anomalous", "setup", "y"]

# Nombres que jamas pueden aparecer en X (incluye resultados y nombres de agentes)
FORBIDDEN_IN_X = set(META_COLUMNS) | {"result", "winner", "reward_0", "reward_1", "agent_0", "agent_1"}

# Condiciones especiales de un Pokemon activo
STATUS_FLAGS = ("asleep", "burned", "confused", "paralyzed", "poisoned")

# Magnitudes para las que se calcula la diferencia propio menos oponente
DIFF_KEYS = ("hand", "prizes", "bench_n", "total_hp", "total_energies", "deck")


def acting_player(step):
    """Devuelve el indice (0 o 1) del jugador que actua en este paso, o None.
    El jugador que actua es el que tiene status ACTIVE; el otro esta INACTIVE.
    """
    for j, entry in enumerate(step):
        if entry["status"] == "ACTIVE":
            return j
    return None


def _mon_stats(mon):
    """Resume un Pokemon en juego: vida, energias, herramientas y marcas de evolucion."""
    hp = mon.get("hp", SENTINEL)
    max_hp = mon.get("maxHp", SENTINEL)
    return {
        "hp": hp,
        "max_hp": max_hp,
        "energies": len(mon.get("energies") or []),
        "tools": len(mon.get("tools") or []),
        "evolved": int(bool(mon.get("preEvolution"))),
        "new": int(bool(mon.get("appearThisTurn"))),
    }


def _side(p, pre):
    """Caracteristicas de un jugador. 'pre' es el prefijo: own_ (propio) u opp_ (oponente)."""
    # El Pokemon activo es el primero de la lista; puede no existir
    active = p["active"][0] if p.get("active") else None
    # La banca puede traer espacios vacios (None); se descartan
    bench = [m for m in (p.get("bench") or []) if m]
    a = _mon_stats(active) if active else None
    b = [_mon_stats(m) for m in bench]
    # Todos los Pokemon en juego: activo mas banca
    mons = ([a] if a else []) + b

    f = {
        f"{pre}deck": p["deckCount"],
        f"{pre}hand": p["handCount"],  # solo el tamano de la mano, nunca su contenido
        f"{pre}discard": len(p.get("discard") or []),
        # Los premios llegan como lista de nulos: lo que importa es cuantos quedan (el largo)
        f"{pre}prizes": len(p.get("prize") or []),
        f"{pre}bench_n": len(bench),
        # Indicador de que existe Pokemon activo; si no, los campos activos valen SENTINEL
        f"{pre}active_present": int(a is not None),
        f"{pre}active_hp": a["hp"] if a else SENTINEL,
        f"{pre}active_max_hp": a["max_hp"] if a else SENTINEL,
        f"{pre}active_hp_ratio": (a["hp"] / a["max_hp"]) if a and a["max_hp"] > 0 else SENTINEL,
        f"{pre}active_energies": a["energies"] if a else SENTINEL,
        f"{pre}active_tools": a["tools"] if a else SENTINEL,
        f"{pre}active_evolved": a["evolved"] if a else SENTINEL,
        f"{pre}active_new": a["new"] if a else SENTINEL,
        # Totales sobre la banca y sobre todo el tablero
        f"{pre}bench_hp": sum(m["hp"] for m in b),
        f"{pre}bench_energies": sum(m["energies"] for m in b),
        f"{pre}total_hp": sum(m["hp"] for m in mons),
        f"{pre}total_energies": sum(m["energies"] for m in mons),
        f"{pre}total_tools": sum(m["tools"] for m in mons),
        # Cuantos Pokemon tienen vida por debajo de su maximo
        f"{pre}damaged": sum(1 for m in mons if 0 <= m["hp"] < m["max_hp"]),
    }
    # Condiciones especiales (dormido, quemado, confundido, paralizado, envenenado)
    for flag in STATUS_FLAGS:
        f[f"{pre}{flag}"] = int(bool(p.get(flag)))
    return f


def extract_features(cur):
    """Caracteristicas de un estado, desde la perspectiva del jugador que actua.
    'cur' es observation["current"] del jugador activo en ese paso.
    """
    me = cur["yourIndex"]
    own = cur["players"][me]
    opp = cur["players"][1 - me]

    # Banderas del turno actual
    f = {
        "turn_action_count": cur["turnActionCount"],
        "energy_attached": int(bool(cur["energyAttached"])),
        "retreated": int(bool(cur["retreated"])),
        "supporter_played": int(bool(cur["supporterPlayed"])),
        "stadium_played": int(bool(cur["stadiumPlayed"])),
        "stadium_in_play": int(bool(cur.get("stadium"))),
        "first_player_is_me": int(cur["firstPlayer"] == me),
    }
    f.update(_side(own, "own_"))
    f.update(_side(opp, "opp_"))
    # Diferencias propio menos oponente: resumen directo de quien va ganando
    for k in DIFF_KEYS:
        f[f"diff_{k}"] = f[f"own_{k}"] - f[f"opp_{k}"]
    return f


def game_rows(game, day):
    """Convierte una partida (JSON ya cargado) en una lista de filas de estado."""
    info = game.get("info") or {}
    game_id = int(info.get("EpisodeId", -1))
    rewards = game.get("rewards") or [None, None]
    # Empates o recompensas ausentes: la partida completa se excluye
    if rewards[0] is None or rewards[1] is None or rewards[0] == rewards[1]:
        return []
    statuses = game.get("statuses") or []
    # Marca de partida anomala: algun jugador no termino en estado DONE
    anomalous = int(any(s != "DONE" for s in statuses))

    rows = []
    for i, step in enumerate(game.get("steps", [])):
        # Se toma la vista del jugador que actua en este paso
        j = acting_player(step)
        if j is None:
            continue
        cur = step[j]["observation"].get("current")
        if not cur:
            continue
        me = cur["yourIndex"]
        r = rewards[me]
        if r is None or r == 0:
            continue
        row = {
            "game_id": game_id,
            "day": day,
            "step": i,
            "turn": cur["turn"],
            "acting_index": me,
            "anomalous": anomalous,
            # Turno 0 es la preparacion (premios sin repartir, tablero vacio)
            "setup": int(cur["turn"] == 0),
            # Etiqueta: 1 si el jugador que actua termina ganando
            "y": int(r > 0),
        }
        row.update(extract_features(cur))
        rows.append(row)
    return rows


def feature_columns(columns):
    """Devuelve las columnas que van a X (todo menos las meta).
    Falla si alguna columna prohibida se cuela: es la defensa contra fuga de informacion.
    """
    cols = [c for c in columns if c not in META_COLUMNS]
    bad = [c for c in cols if c in FORBIDDEN_IN_X]
    if bad:
        raise ValueError(f"columnas prohibidas en X: {bad}")
    return cols