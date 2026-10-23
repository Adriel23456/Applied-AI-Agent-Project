"""B2: cobertura completa, pesos entre lotes, fuga y equivalencia de métricas."""

import json
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ptcg_wp.baselines import ScenarioStream, weights_by_game
from ptcg_wp.b2 import b2_group_cv, fit_b2_candidates_val, _collect_rows
from ptcg_wp.b2_streaming import (evaluate_stream, fit_incremental, game_counts,
                                  prepare_training, training_diagnostics)


FEATURES = ["x", "z"]


@pytest.fixture
def corpus(tmp_path):
    rng = np.random.default_rng(18)
    rows, splits = [], []
    for game in range(22):
        split = "train" if game < 16 else "val" if game < 20 else "test" if game == 20 else "calib"
        splits.append({"game_id": f"g{game}", "split_A": split})
        for turn in range(1, 25 + 3 * game):
            x, z = rng.normal(size=2)
            y = int(rng.random() < expit(0.8 * x - 0.4 * z + 0.2))
            rows.append(dict(game_id=f"g{game}", turn=turn, setup=0, decided=0,
                             y=y, x=x, z=z))
    frame = pd.DataFrame(rows)
    # Incluso una partida repartida entre archivos debe sumar el mismo peso.
    frame.iloc[::2].to_parquet(tmp_path / "estados_1.parquet", index=False, row_group_size=31)
    frame.iloc[1::2].to_parquet(tmp_path / "estados_2.parquet", index=False, row_group_size=31)
    pd.DataFrame(splits).to_parquet(tmp_path / "particiones.parquet", index=False)
    return tmp_path, frame, pd.DataFrame(splits).set_index("game_id")["split_A"]


@pytest.mark.parametrize("batch_size", [7, 64, 4096])
def test_batches_and_exact_quantiles(corpus, batch_size):
    directory, frame, splits = corpus
    stream = ScenarioStream(directory, "A", tuple(FEATURES), batch_size=batch_size)
    train = frame.loc[frame.game_id.map(splits).eq("train")]
    np.testing.assert_allclose(stream.cuts, np.quantile(train.turn, [1 / 3, 2 / 3]))
    batches = list(stream.iter_batches("train"))
    assert all(0 < len(batch) <= batch_size for batch in batches)
    assert sum(map(len, batches)) == len(train)
    counts = game_counts(stream, "train")
    pd.testing.assert_series_equal(counts["global"].sort_index(),
                                   train.game_id.value_counts().sort_index(), check_names=False)
    assert set(pd.concat(batches).game_id) == set(train.game_id)
    with pytest.raises(ValueError, match="train y val"):
        list(stream.iter_batches("test"))


def test_scaler_and_weights_use_complete_games(corpus, tmp_path):
    directory, frame, splits = corpus
    stream = ScenarioStream(directory, "A", tuple(FEATURES), batch_size=29)
    games = ["g0", "g3", "g15"]
    cache = tmp_path / "cache"
    cache.mkdir()
    scaler, paths, n_rows, n_games = prepare_training(stream, FEATURES, games, cache)
    train = frame.loc[frame.game_id.isin(games)]
    weights = weights_by_game(train.game_id)
    reference = StandardScaler().fit(train[FEATURES], sample_weight=weights)
    np.testing.assert_allclose(scaler.mean_, reference.mean_, atol=1e-12)
    np.testing.assert_allclose(scaler.var_, reference.var_, atol=1e-12)
    assert n_rows == len(train) and n_games == 3
    total_rows, weight_sum = 0, 0
    for path in paths:
        with np.load(path) as batch:
            assert len(batch["x"]) <= stream.batch_size
            total_rows += len(batch["x"])
            weight_sum += batch["weights"].sum()
    assert total_rows == n_rows
    assert weight_sum == pytest.approx(n_rows)


class TiedPredictions:
    def predict_proba(self, x):
        # Fuerza empates, incluidos extremos, y clases mezcladas dentro del empate.
        p = np.where(x[:, 0] < -0.5, 0.0, np.where(x[:, 0] > 0.5, 1.0, 0.5))
        return np.column_stack([1 - p, p])


def test_disk_metrics_match_sklearn_with_ties_and_stage_weights(corpus, tmp_path):
    directory, _, _ = corpus
    stream = ScenarioStream(directory, "A", tuple(FEATURES), batch_size=17)
    model = TiedPredictions()
    rows = evaluate_stream(model, stream, FEATURES, "val", None, tmp_path, {})
    val = pd.concat(stream.iter_batches("val"))
    for row in rows:
        part = val if row["etapa"] == "global" else val.loc[val.stage.eq(row["etapa"])]
        weights = weights_by_game(part.game_id)
        probability = np.clip(model.predict_proba(part[FEATURES].to_numpy())[:, 1], 1e-15, 1-1e-15)
        assert row["auc"] == pytest.approx(roc_auc_score(part.y, probability, sample_weight=weights), abs=1e-12)
        assert row["log_loss"] == pytest.approx(log_loss(part.y, probability, sample_weight=weights), abs=1e-12)
        assert row["brier"] == pytest.approx(brier_score_loss(part.y, probability, sample_weight=weights), abs=1e-12)
        assert row["n_partidas"] == part.game_id.nunique()
        assert row["n_estados"] == len(part)
    assert not list(tmp_path.glob("predictions-*.sqlite"))


@pytest.mark.parametrize("c_value", [0.01, 1.0, 100.0])
def test_sgd_matches_weighted_logistic_objective(corpus, tmp_path, c_value):
    directory, _, _ = corpus
    stream = ScenarioStream(directory, "A", tuple(FEATURES), batch_size=128)
    cache = tmp_path / "cache"
    cache.mkdir()
    scaler, paths, n_rows, n_games = prepare_training(stream, FEATURES, None, cache)
    model, info = fit_incremental(scaler, paths, n_rows, n_games, c_value,
                                  max_iter=150, eta0=0.2, tolerance=1e-3, verbose=False)
    train = pd.concat(stream.iter_batches("train"))
    x = scaler.transform(train[FEATURES].to_numpy())
    weights = weights_by_game(train.game_id)
    reference = LogisticRegression(C=c_value, tol=1e-10, max_iter=1000).fit(x, train.y, sample_weight=weights)
    fitted = model.named_steps["logit"]
    assert fitted.alpha == pytest.approx(1 / (c_value * n_games))
    actual, gradient = training_diagnostics(fitted, paths, n_rows)
    scores = reference.decision_function(x)
    expected = (np.dot(weights, np.logaddexp(0, scores) - train.y * scores) / n_games
                + np.sum(reference.coef_**2) / (2 * c_value * n_games))
    assert actual - expected < 2e-4
    assert gradient < 0.01
    assert info["convergencia"] == (gradient <= 1e-3)
    np.testing.assert_allclose(model.predict_proba(train[FEATURES].to_numpy()),
                               reference.predict_proba(x), atol=0.025)


def test_cv_covers_all_games_and_final_fit_saves_models(corpus, tmp_path, monkeypatch):
    directory, frame, splits = corpus
    stream = ScenarioStream(directory, "A", tuple(FEATURES), batch_size=100)

    def forbidden(*args, **kwargs):
        raise AssertionError("B2 no debe usar el iterador diario ni concatenar todo train")

    monkeypatch.setattr(ScenarioStream, "__iter__", forbidden)
    monkeypatch.setattr("ptcg_wp.b2._collect_rows", forbidden)
    cache, output = tmp_path / "cache", tmp_path / "output"
    cache.mkdir()
    cv = b2_group_cv(stream, FEATURES, c_values=[1], n_splits=2, max_iter=2,
                     cache_dir=cache, output_dir=output, verbose=False)
    global_rows = cv.loc[cv.etapa.eq("global")]
    assert global_rows.n_partidas.sum() == 16
    assert global_rows.n_estados.sum() == frame.game_id.map(splits).eq("train").sum()
    assert (global_rows.fraccion_train == 1).all()
    assert (global_rows.n_partidas_fit == 8).all()
    assert (global_rows.partidas_train_muestra == 16).all()
    assert not list(cache.iterdir())
    assert (output / "b2_cv_A.csv").exists()
    val = fit_b2_candidates_val(stream, FEATURES, [1], max_iter=2, cache_dir=cache,
                               output_dir=output, verbose=False)
    assert (val.n_partidas_fit == 16).all()
    assert val.loc[val.etapa.eq("global"), "n_partidas"].iloc[0] == 4
    artifact = joblib.load(output / "b2_A_C1.joblib")
    assert artifact["features"] == FEATURES
    assert artifact["n_partidas_fit"] == 16
    assert not list(cache.iterdir())
    with pytest.raises(ValueError, match="train_games"):
        b2_group_cv(stream, FEATURES, train_games=["g0", "g20"], verbose=False)


def test_training_does_not_use_heldout_values(corpus, tmp_path):
    directory, _, _ = corpus
    stream = ScenarioStream(directory, "A", tuple(FEATURES), batch_size=128)
    games = ["g0", "g1", "g2", "g3"]
    cache1, cache2 = tmp_path / "cache1", tmp_path / "cache2"
    cache1.mkdir()
    cache2.mkdir()
    prepared = prepare_training(stream, FEATURES, games, cache1)
    model1, info1 = fit_incremental(*prepared, 1.0, max_iter=2, verbose=False)
    for path in stream.files:
        frame = pd.read_parquet(path)
        held = ~frame.game_id.isin(games)
        frame.loc[held, ["x", "z"]] = 1e9
        frame.loc[held, "y"] = 1 - frame.loc[held, "y"]
        # Conserva los lotes físicos para aislar solo el efecto de datos retenidos.
        frame.to_parquet(path, index=False, row_group_size=31)
    prepared = prepare_training(stream, FEATURES, games, cache2)
    model2, info2 = fit_incremental(*prepared, 1.0, max_iter=2, verbose=False)
    np.testing.assert_array_equal(model1.named_steps["scale"].mean_, model2.named_steps["scale"].mean_)
    np.testing.assert_array_equal(model1.named_steps["logit"].coef_, model2.named_steps["logit"].coef_)
    assert info1 == info2


def test_exception_cleans_temporary_cache(corpus, tmp_path, monkeypatch):
    directory, _, _ = corpus
    stream = ScenarioStream(directory, "A", tuple(FEATURES), batch_size=256)
    cache = tmp_path / "cache"
    cache.mkdir()

    def fail(*args, **kwargs):
        raise RuntimeError("fallo simulado")

    monkeypatch.setattr("ptcg_wp.b2.evaluate_stream", fail)
    with pytest.raises(RuntimeError, match="simulado"):
        b2_group_cv(stream, FEATURES, c_values=[1], n_splits=2, max_iter=1,
                    cache_dir=cache, verbose=False)
    assert not list(cache.iterdir())


def test_cv_resumes_when_interruption_left_only_manifest(corpus, tmp_path, monkeypatch):
    directory, _, _ = corpus
    stream = ScenarioStream(directory, "A", tuple(FEATURES), batch_size=256)
    cache, output = tmp_path / "cache", tmp_path / "output"
    cache.mkdir()

    def fail(*args, **kwargs):
        raise RuntimeError("fallo simulado antes de completar el primer pliegue")

    monkeypatch.setattr("ptcg_wp.b2.fit_incremental", fail)
    with pytest.raises(RuntimeError, match="fallo simulado"):
        b2_group_cv(stream, FEATURES, c_values=[1], n_splits=2, max_iter=1,
                    cache_dir=cache, output_dir=output, verbose=False)
    assert (output / "b2_cv_A_manifest.json").exists()
    assert not (output / "b2_cv_A.csv").exists()

    monkeypatch.setattr("ptcg_wp.b2.fit_incremental", fit_incremental)
    resumed = b2_group_cv(stream, FEATURES, c_values=[1], n_splits=2, max_iter=1,
                          cache_dir=cache, output_dir=output, verbose=False)
    complete = resumed.loc[resumed.etapa.eq("global")]
    assert set(complete.fold) == {1, 2}
    assert (output / "b2_cv_A.csv").exists()


def test_cv_checkpoints_each_c_and_skips_it_after_interruption(corpus, tmp_path, monkeypatch):
    directory, _, _ = corpus
    stream = ScenarioStream(directory, "A", tuple(FEATURES), batch_size=256)
    cache, output = tmp_path / "cache", tmp_path / "output"
    cache.mkdir()
    original_fit = fit_incremental

    def interrupt_on_second_c(scaler, paths, n_rows, n_games, c_value, *args, **kwargs):
        if c_value == 0.1:
            raise RuntimeError("interrupción simulada antes del segundo C")
        return original_fit(scaler, paths, n_rows, n_games, c_value, *args, **kwargs)

    monkeypatch.setattr("ptcg_wp.b2.fit_incremental", interrupt_on_second_c)
    with pytest.raises(RuntimeError, match="segundo C"):
        b2_group_cv(stream, FEATURES, c_values=[1.0, 0.1], n_splits=2, max_iter=1,
                    cache_dir=cache, output_dir=output, verbose=False)
    saved = pd.read_csv(output / "b2_cv_A.csv")
    assert set(saved.loc[saved.etapa.eq("global"), ["fold", "C"]].itertuples(index=False, name=None)) == {(1, 1.0)}

    resumed_calls = []

    def track_resume(scaler, paths, n_rows, n_games, c_value, *args, **kwargs):
        resumed_calls.append(c_value)
        return original_fit(scaler, paths, n_rows, n_games, c_value, *args, **kwargs)

    monkeypatch.setattr("ptcg_wp.b2.fit_incremental", track_resume)
    resumed = b2_group_cv(stream, FEATURES, c_values=[1.0, 0.1], n_splits=2, max_iter=1,
                          cache_dir=cache, output_dir=output, verbose=False)
    assert resumed_calls == [0.1, 1.0, 0.1]
    complete = resumed.loc[resumed.etapa.eq("global")]
    assert set(complete.fold) == {1, 2}
    assert set(complete.C) == {1.0, 0.1}


def test_val_resumes_when_interruption_left_only_manifest(corpus, tmp_path, monkeypatch):
    directory, _, _ = corpus
    stream = ScenarioStream(directory, "A", tuple(FEATURES), batch_size=256)
    cache, output = tmp_path / "cache", tmp_path / "output"
    cache.mkdir()

    def fail(*args, **kwargs):
        raise RuntimeError("interrupción simulada en el primer finalista")

    monkeypatch.setattr("ptcg_wp.b2.fit_incremental", fail)
    with pytest.raises(RuntimeError, match="primer finalista"):
        fit_b2_candidates_val(stream, FEATURES, [1.0], max_iter=1,
                              cache_dir=cache, output_dir=output, verbose=False)
    assert (output / "b2_val_A_manifest.json").exists()
    assert not (output / "b2_val_A.csv").exists()

    monkeypatch.setattr("ptcg_wp.b2.fit_incremental", fit_incremental)
    resumed = fit_b2_candidates_val(stream, FEATURES, [1.0], max_iter=1,
                                    cache_dir=cache, output_dir=output, verbose=False)
    assert set(resumed.loc[resumed.etapa.eq("global"), "C"]) == {1.0}
    assert (output / "b2_val_A.csv").exists()


def test_row_demo_has_a_hard_row_guard(corpus):
    directory, _, _ = corpus
    stream = ScenarioStream(directory, "A", tuple(FEATURES), batch_size=16)
    with pytest.raises(ValueError, match="demo por fila"):
        _collect_rows(stream, FEATURES, "train", max_rows=20)


def test_notebook_b2_cells_compile_and_default_to_full_coverage():
    notebook = json.loads((Path(__file__).parents[1] / "notebooks/02_baselines.ipynb").read_text())
    cells = {cell["id"]: "".join(cell["source"]) for cell in notebook["cells"]}
    for name in ("b2-config", "b2-execute"):
        compile(cells[name], name, "exec")
        assert "sample_train_games(" not in cells[name]
        assert "B2_MAX_TRAIN_GAMES" not in cells[name]


def test_arrow_buffers_do_not_accumulate_across_row_groups(tmp_path):
    rng = np.random.default_rng(2026)
    features = [f"x{i}" for i in range(32)]
    group_rows = 1024
    frame = pd.DataFrame(rng.normal(size=(group_rows, len(features))), columns=features)
    frame["game_id"] = 0
    frame["turn"] = np.arange(group_rows)
    frame["setup"] = frame["decided"] = 0
    frame["y"] = np.arange(group_rows) % 2
    table = pa.Table.from_pandas(frame, preserve_index=False)
    with pq.ParquetWriter(tmp_path / "estados_1.parquet", table.schema) as writer:
        for _ in range(32):
            writer.write_table(table)
    pd.DataFrame({"game_id": [0], "split_A": ["train"]}).to_parquet(
        tmp_path / "particiones.parquet", index=False
    )
    stream = ScenarioStream(tmp_path, "A", tuple(features), batch_size=256)
    baseline = pa.total_allocated_bytes()
    peak, rows = 0, 0
    for batch in stream.iter_batches("train"):
        peak = max(peak, pa.total_allocated_bytes() - baseline)
        rows += len(batch)
    assert rows == group_rows * 32
    # Margen holgado de 16 grupos para buffers internos; nunca retener los 32.
    assert peak < 16 * group_rows * len(features) * 8
