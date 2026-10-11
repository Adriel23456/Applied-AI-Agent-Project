"""Pruebas automaticas de los invariantes de fuga y de la etiqueta.

Se usan partidas sinteticas con la misma forma que el JSON de Kaggle, asi que
corren en segundos, sin descargar nada:  python -m pytest -q tests
"""

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ptcg_wp.features import (  # noqa: E402
    CARD_COLUMNS, FORBIDDEN_IN_X, META_COLUMNS, deck_signatures, feature_columns, game_rows, usable,
)


# ---------- Constructores de partidas sinteticas ----------

def mon(card, hp=100, max_hp=100):
    """Un Pokemon en juego con los campos del JSON real."""
    return {"appearThisTurn": False, "energies": [], "energyCards": [], "hp": hp, "id": card,
            "maxHp": max_hp, "playerIndex": 0, "preEvolution": [], "serial": card, "tools": []}


def player(active=1, bench=(), prizes=6, hand_count=5, deck=40):
    """Un jugador. La mano y los premios van como en la vista real: ocultos (None)."""
    return {"active": [mon(active)] if active else [], "bench": [mon(b) for b in bench],
            "deckCount": deck, "handCount": hand_count, "hand": None, "discard": [],
            "prize": [None] * prizes, "asleep": False, "burned": False, "confused": False,
            "paralyzed": False, "poisoned": False, "benchMax": 5}


def current(me, turn, players):
    """observation.current tal como lo ve el jugador 'me'."""
    return {"yourIndex": me, "turn": turn, "players": players, "firstPlayer": 0,
            "turnActionCount": 0, "energyAttached": False, "retreated": False,
            "supporterPlayed": False, "stadiumPlayed": False, "stadium": [], "result": 0}


def game(rewards=(1, -1), turns=(0, 1, 1, 2, 2, 3)):
    """Partida con un paso por turno indicado; actua alternadamente el jugador 0 y el 1."""
    steps = []
    for i, t in enumerate(turns):
        j = i % 2
        players = [player(active=10, bench=(11,)), player(active=20, bench=(21, 22))]
        cur = current(j, t, players)
        entry_on = {"status": "ACTIVE", "observation": {"current": cur}}
        entry_off = {"status": "INACTIVE", "observation": {"current": None}}
        steps.append([entry_on, entry_off] if j == 0 else [entry_off, entry_on])
    return {"info": {"EpisodeId": 1}, "rewards": list(rewards), "statuses": ["DONE", "DONE"],
            "steps": steps}


def x_part(rows):
    """Solo las caracteristicas (lo que veria el modelo) de cada fila."""
    return [{k: v for k, v in r.items() if k not in META_COLUMNS} for r in rows]


# ---------- Etiqueta y exclusiones ----------

def test_label_follows_reward_of_acting_player():
    rows = game_rows(game(rewards=(1, -1)), "d")
    assert rows
    for r in rows:
        assert r["y"] == int(r["acting_index"] == 0)


@pytest.mark.parametrize("rewards", [(0, 0), (-1, -1), (1, 1), (None, 1)])
def test_draws_and_missing_rewards_are_excluded(rewards):
    assert game_rows(game(rewards=rewards), "d") == []


def test_setup_and_decided_flags():
    g = game()
    # Paso 3: el jugador 1 ya no tiene premios (la partida esta resuelta)
    g["steps"][3][1]["observation"]["current"]["players"][1]["prize"] = []
    # Paso 4: el jugador 1 ya no tiene Pokemon en juego
    g["steps"][4][0]["observation"]["current"]["players"][1]["active"] = []
    g["steps"][4][0]["observation"]["current"]["players"][1]["bench"] = []
    rows = {r["step"]: r for r in game_rows(g, "d")}
    assert rows[0]["setup"] == 1 and rows[0]["decided"] == 0
    assert rows[3]["decided"] == 1
    assert rows[4]["decided"] == 1
    assert rows[5]["decided"] == 0


def test_usable_drops_setup_and_decided():
    import pandas as pd
    g = game()
    g["steps"][3][1]["observation"]["current"]["players"][1]["prize"] = []
    df = pd.DataFrame(game_rows(g, "d"))
    kept = usable(df)
    assert (kept["setup"] == 0).all() and (kept["decided"] == 0).all()
    assert set(kept["step"]) == {1, 2, 4, 5}


# ---------- Invariantes de fuga ----------

def test_hidden_information_does_not_change_features():
    """Llenar la mano del oponente y los premios con cartas reales no debe cambiar X."""
    g = game()
    base = x_part(game_rows(g, "d"))
    g2 = copy.deepcopy(g)
    for step in g2["steps"]:
        for e in step:
            cur = e["observation"]["current"]
            if not cur:
                continue
            me = cur["yourIndex"]
            opp = cur["players"][1 - me]
            opp["hand"] = [{"id": 999, "serial": s} for s in range(opp["handCount"])]
            for p in cur["players"]:
                p["prize"] = [{"id": 999, "serial": s} for s in range(len(p["prize"]))]
            cur["players"][me]["hand"] = [{"id": 777, "serial": s} for s in range(5)]
    assert x_part(game_rows(g2, "d")) == base


def test_result_and_rewards_do_not_change_features():
    """Cambiar quien gana o el campo result solo puede cambiar y, nunca X."""
    g = game(rewards=(1, -1))
    g2 = copy.deepcopy(g)
    g2["rewards"] = [-1, 1]
    for step in g2["steps"]:
        for e in step:
            if e["observation"]["current"]:
                e["observation"]["current"]["result"] = 1
    a, b = game_rows(g, "d"), game_rows(g2, "d")
    assert x_part(a) == x_part(b)
    assert [r["y"] for r in a] == [1 - r["y"] for r in b]


def test_future_steps_do_not_change_past_features():
    """Cortar la partida despues del paso k no cambia las filas de los pasos <= k."""
    g = game()
    full = game_rows(g, "d")
    g2 = copy.deepcopy(g)
    g2["steps"] = g2["steps"][:3]
    assert x_part(game_rows(g2, "d")) == x_part(full[:3])


def test_forbidden_columns_never_reach_x():
    rows = game_rows(game(), "d")
    cols = feature_columns(list(rows[0].keys()))
    assert not set(cols) & FORBIDDEN_IN_X
    with pytest.raises(ValueError):
        feature_columns(cols + ["winner"])
    with pytest.raises(ValueError):
        feature_columns(cols + ["deck_0"])

def test_card_ids_only_enter_x_when_requested():
    """Los ids de carta (contexto de mazo) no entran al modelo principal, solo a la ablacion."""
    cols = list(game_rows(game(), "d")[0].keys())
    assert not set(CARD_COLUMNS) & set(feature_columns(cols))
    assert set(CARD_COLUMNS) <= set(feature_columns(cols, include_cards=True))
    assert len(feature_columns(cols, include_cards=True)) == len(feature_columns(cols)) + 2

# ---------- Metadatos de mazo ----------

def test_deck_signatures_use_absolute_player_index():
    decks, mains = deck_signatures(game())
    assert decks == ["10-11", "20-21-22"]
    assert mains == [10, 20]