"""Pruebas automaticas de las particiones, la cobertura de cartas y los cortes de etapa.

Usan tablas sinteticas: corren en segundos.  python -m pytest -q tests
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ptcg_wp.splits import (  # noqa: E402
    FUERA, ORDEN, PROPORCIONES, assign_stage, card_coverage, make_splits, stage_cutoffs,
)

DAYS = [f"2026-07-{d:02d}" for d in range(1, 11)]
B_CONFIG = {"excluir": [DAYS[0]], "train": DAYS[1:6], "val": [DAYS[6]], "calib": [DAYS[7]],
            "test": DAYS[8:]}


def fake_data(n=3000, n_mains=40, n_cards=60, seed=0):
    """Tabla de partidas y pares (partida, carta activa) sinteticos.
    Las cartas 1000+ son raras: aparecen en una sola partida cada una.
    """
    rng = np.random.default_rng(seed)
    games = pd.DataFrame({
        "game_id": rng.permutation(np.arange(10_000, 10_000 + n)),
        "day": rng.choice(DAYS, n),
        "n_steps": rng.integers(20, 300, n),
        "main_0": rng.integers(1, n_mains, n),
        "main_1": rng.integers(1, n_mains, n),
    })
    pairs = pd.DataFrame({"game_id": np.repeat(games["game_id"].to_numpy(), 3),
                          "card": rng.integers(1, n_cards, 3 * n)}).drop_duplicates()
    rare = pd.DataFrame({"game_id": games["game_id"].to_numpy()[:20], "card": np.arange(1000, 1020)})
    return games, pd.concat([pairs, rare], ignore_index=True)


def splits_and_report():
    games, pairs = fake_data()
    splits, report = make_splits(games, pairs, B_CONFIG)
    return games, pairs, splits, report


def test_every_game_gets_one_valid_label_per_scenario():
    _, _, splits, _ = splits_and_report()
    for s in ("split_A", "split_B", "split_C"):
        assert splits[s].notna().all()
        assert set(splits[s]) <= set(ORDEN) | {FUERA}
    assert splits["game_id"].is_unique


def test_splits_are_reproducible_with_the_seed():
    _, _, a, ra = splits_and_report()
    _, _, b, rb = splits_and_report()
    assert a.equals(b) and ra == rb


def test_proportions_a():
    _, _, splits, _ = splits_and_report()
    frac = splits["split_A"].value_counts(normalize=True)
    for name, p in PROPORCIONES.items():
        assert abs(frac[name] - p) < 0.015


def test_b_uses_whole_days_in_order_and_excludes_first_day():
    _, _, splits, _ = splits_and_report()
    assert (splits.loc[splits["day"] == DAYS[0], "split_B"] == FUERA).all()
    assert (splits.groupby("day")["split_B"].nunique() == 1).all()
    last_day = {n: splits.loc[splits["split_B"] == n, "day"].max() for n in ORDEN}
    first_day = {n: splits.loc[splits["split_B"] == n, "day"].min() for n in ORDEN}
    for a, b in zip(ORDEN, ORDEN[1:]):
        assert last_day[a] < first_day[b]


def test_c_reserved_mains_never_in_non_test():
    games, _, splits, report = splits_and_report()
    reserved = report["C_reservados"]
    assert reserved
    no_test = splits["split_C"] != "test"
    assert not games.loc[no_test, "main_0"].isin(reserved).any()
    assert not games.loc[no_test, "main_1"].isin(reserved).any()
    assert 0.15 <= (~no_test).mean() <= 0.18


def test_coverage_every_card_in_train_for_a():
    _, pairs, splits, report = splits_and_report()
    train_ids = set(splits.loc[splits["split_A"] == "train", "game_id"])
    train_cards = set(pairs.loc[pairs["game_id"].isin(train_ids), "card"])
    assert set(pairs["card"]) == train_cards
    assert report["A_sin_cubrir"] == []
    assert report["cartas_en_una_sola_partida"] >= 20


def test_coverage_in_c_never_moves_reserved_games():
    games, pairs, splits, report = splits_and_report()
    moved = set(report["C_movidas"])
    reserved = report["C_reservados"]
    moved_games = games[games["game_id"].isin(moved)]
    assert not moved_games["main_0"].isin(reserved).any()
    assert not moved_games["main_1"].isin(reserved).any()


def test_states_of_a_game_never_split():
    games, _, splits, _ = splits_and_report()
    states = pd.DataFrame({"game_id": np.repeat(games["game_id"].to_numpy(), 5)})
    states["split"] = states["game_id"].map(splits.set_index("game_id")["split_A"])
    assert (states.groupby("game_id")["split"].nunique() == 1).all()


def test_stage_cutoffs_and_assignment():
    cuts = stage_cutoffs(np.arange(1, 31))
    stages = assign_stage([1, 15, 30], cuts)
    assert list(stages) == ["inicio", "medio", "final"]


def test_card_coverage_detects_unseen_cards():
    states = pd.DataFrame({"own_active_card": [1, 2, 1, 9], "opp_active_card": [2, 1, 2, 2]})
    cov = card_coverage(states, ["train", "train", "test", "test"])
    assert cov.loc["train", "pct_filas_carta_no_vista"] == 0
    assert cov.loc["test", "pct_filas_carta_no_vista"] == 50
    assert cov.loc["test", "cartas_no_vistas"] == 1