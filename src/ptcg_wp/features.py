SENTINEL = -1

META_COLUMNS = ["game_id", "day", "step", "turn", "acting_index", "anomalous", "setup", "y"]

FORBIDDEN_IN_X = set(META_COLUMNS) | {"result", "winner", "reward_0", "reward_1", "agent_0", "agent_1"}

STATUS_FLAGS = ("asleep", "burned", "confused", "paralyzed", "poisoned")

DIFF_KEYS = ("hand", "prizes", "bench_n", "total_hp", "total_energies", "deck")


def acting_player(step):
    for j, entry in enumerate(step):
        if entry["status"] == "ACTIVE":
            return j
    return None


def _mon_stats(mon):
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
    active = p["active"][0] if p.get("active") else None
    bench = [m for m in (p.get("bench") or []) if m]
    a = _mon_stats(active) if active else None
    b = [_mon_stats(m) for m in bench]
    mons = ([a] if a else []) + b

    f = {
        f"{pre}deck": p["deckCount"],
        f"{pre}hand": p["handCount"],
        f"{pre}discard": len(p.get("discard") or []),
        f"{pre}prizes": len(p.get("prize") or []),
        f"{pre}bench_n": len(bench),
        f"{pre}active_present": int(a is not None),
        f"{pre}active_hp": a["hp"] if a else SENTINEL,
        f"{pre}active_max_hp": a["max_hp"] if a else SENTINEL,
        f"{pre}active_hp_ratio": (a["hp"] / a["max_hp"]) if a and a["max_hp"] > 0 else SENTINEL,
        f"{pre}active_energies": a["energies"] if a else SENTINEL,
        f"{pre}active_tools": a["tools"] if a else SENTINEL,
        f"{pre}active_evolved": a["evolved"] if a else SENTINEL,
        f"{pre}active_new": a["new"] if a else SENTINEL,
        f"{pre}bench_hp": sum(m["hp"] for m in b),
        f"{pre}bench_energies": sum(m["energies"] for m in b),
        f"{pre}total_hp": sum(m["hp"] for m in mons),
        f"{pre}total_energies": sum(m["energies"] for m in mons),
        f"{pre}total_tools": sum(m["tools"] for m in mons),
        f"{pre}damaged": sum(1 for m in mons if 0 <= m["hp"] < m["max_hp"]),
    }
    for flag in STATUS_FLAGS:
        f[f"{pre}{flag}"] = int(bool(p.get(flag)))
    return f


def extract_features(cur):
    me = cur["yourIndex"]
    own = cur["players"][me]
    opp = cur["players"][1 - me]

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
    for k in DIFF_KEYS:
        f[f"diff_{k}"] = f[f"own_{k}"] - f[f"opp_{k}"]
    return f


def game_rows(game, day):
    info = game.get("info") or {}
    game_id = int(info.get("EpisodeId", -1))
    rewards = game.get("rewards") or [None, None]
    statuses = game.get("statuses") or []
    anomalous = int(any(s != "DONE" for s in statuses))

    rows = []
    for i, step in enumerate(game.get("steps", [])):
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
            "setup": int(cur["turn"] == 0),
            "y": int(r > 0),
        }
        row.update(extract_features(cur))
        rows.append(row)
    return rows


def feature_columns(columns):
    cols = [c for c in columns if c not in META_COLUMNS]
    bad = [c for c in cols if c in FORBIDDEN_IN_X]
    if bad:
        raise ValueError(f"forbidden columns in X: {bad}")
    return cols