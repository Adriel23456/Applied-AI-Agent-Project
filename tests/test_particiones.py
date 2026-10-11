"""Pruebas automaticas de las particiones, los cortes de etapa y la cobertura de cartas.

Usan una tabla de partidas sintetica: corren en segundos.  python -m pytest -q tests
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ptcg_wp.splits import (  # noqa: E402
    ORDEN, PROPORCIONES, assign_stage, card_coverage, make_splits, stage_cutoffs,
)


def fake_games(n=3000, n_days=10, n_mains=40, seed=0):
    """Tabla de partidas sintetica con la forma de partidas_<dia>.parquet."""
    rng = np.random.default_rng(seed)
    days = [f"2026-07-{d:02d}" for d in range(1, n_days + 1)]
    return pd.DataFrame({
        "game_id": rng.permutation(np.arange(10_000, 10_000 + n)),
        "day": rng.choice(days, n),
        "main_0": rng.integers(1, n_mains, n),
        "main_1": rng.integers(1, n_mains, n),
    })


def test_every_game_gets_one_valid_label_per_scenario():
    splits, _ = make_splits(fake_games())
    for s in ("split_A", "split_B", "split_C"):
        assert splits[s].notna().all()
        assert set(splits[s]) <= set(ORDEN)
    assert splits["game_id"].is_unique


def test_splits_are_reproducible_with_the_seed():
    a, ra = make_splits(fake_games())
    b, rb = make_splits(fake_games())
    assert a.equals(b) and ra == rb


def test_proportions_a_and_b():
    splits, _ = make_splits(fake_games())
    for s in ("split_A", "split_B"):
        frac = splits[s].value_counts(normalize=True)
        for name, p in PROPORCIONES.items():
            assert abs(frac[name] - p) < 0.01


def test_b_is_chronological():
    games = fake_games()
    splits, _ = make_splits(games)
    rank = pd.Series(np.lexsort((games["game_id"], games["day"])).argsort(), index=games.index)
    limits = [(rank[splits["split_B"] == n].min(), rank[splits["split_B"] == n].max()) for n in ORDEN]
    for (_, hi), (lo, _) in zip(limits, limits[1:]):
        assert hi < lo


def test_c_reserved_mains_never_in_non_test():
    games = fake_games()
    splits, reserved = make_splits(games)
    assert reserved
    no_test = splits["split_C"] != "test"
    assert not games.loc[no_test, "main_0"].isin(reserved).any()
    assert not games.loc[no_test, "main_1"].isin(reserved).any()
    assert 0.15 <= (~no_test).mean() <= 0.18


def test_states_of_a_game_never_split():
    games = fake_games(n=200)
    splits, _ = make_splits(games)
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