"""Sequential full-data run of the B2 finalist check followed by B3 and B4."""

from pathlib import Path
from tempfile import TemporaryDirectory
import gc
import json

import pandas as pd
import pyarrow.parquet as pq

from ptcg_wp.b2 import b2_group_cv, fit_b2_candidates_val, summarize_b2_cv
from ptcg_wp.b3 import b3_optuna_cv, fit_b3_candidates_val
from ptcg_wp.b4 import (b4_optuna_cv, fit_b4_candidates_val,
                        materialize_split)
from ptcg_wp.baselines import ScenarioStream
from ptcg_wp.checkpoints import atomic_csv, atomic_json, stable_digest
from ptcg_wp.features import feature_columns


DEFAULT_B2_FINALISTS = {
    "A": (1.0, 0.1),
    "B": (1.0, 0.1),
    "C": (1.0, 0.1),
}


def run_sequential_pipeline(data_dir, checkpoint_root, batch_size=32768,
                            b2_max_epochs=600, b2_eta0=0.05,
                            b2_gradient_tol=1e-3, b3_trials=10,
                            b3_n_jobs=2, b4_trials=10, b4_max_iter=500,
                            b4_patience=30, max_ram_gib=10.0,
                            seed=2026, verbose=True):
    """Run B2 finalists, then B3, then B4, persisting each stage as it finishes.

    B2 uses the agreed C finalists (1.0 and 0.1) in each scenario. They are
    intentionally fixed here so this extended run checks training stability
    rather than choosing a different set before seeing its results.
    """
    data_dir, checkpoint_root = Path(data_dir), Path(checkpoint_root)
    schema = pq.ParquetFile(sorted(data_dir.glob("estados_*.parquet"))[0]).schema.names
    features = feature_columns(schema)
    outputs = {}
    status_path = checkpoint_root / "pipeline_status.json"
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}

    def run_phase(name, config, action):
        fingerprint = stable_digest(config)
        saved = status.get(name, {})
        if saved.get("fingerprint") == fingerprint and saved.get("state") == "complete":
            if verbose:
                print(f"{name}: ya completado; se omite", flush=True)
            return False
        if verbose:
            if saved.get("state") == "running":
                print(f"{name}: quedó interrumpido; continúo desde sus checkpoints", flush=True)
            else:
                print(f"{name}: pendiente; iniciando", flush=True)
        status[name] = {"state": "running", "fingerprint": fingerprint}
        atomic_json(status, status_path)
        action()
        status[name] = {"state": "complete", "fingerprint": fingerprint}
        atomic_json(status, status_path)
        return True

    if verbose:
        completed = [name for name, value in status.items() if value.get("state") == "complete"]
        running = [name for name, value in status.items() if value.get("state") == "running"]
        print(f"Checkpoint pipeline: {len(completed)} fases completas; "
              f"fases interrumpidas: {running or 'ninguna'}", flush=True)

    for scenario in ("A", "B", "C"):
        finals = DEFAULT_B2_FINALISTS[scenario]
        # Keep this run separate from earlier checkpoints made with different C finalists.
        b2_dir = checkpoint_root / "b2" / "finalists_c_1_0_0_1_600" / f"escenario_{scenario}"
        b2_config = {"scenario": scenario, "finalists": finals,
                     "features_sha256": stable_digest(list(features)),
                     "batch_size": batch_size, "max_epochs": b2_max_epochs,
                     "eta0": b2_eta0, "gradient_tolerance": b2_gradient_tol,
                     "seed": seed}

        def run_b2_scenario():
            stream = ScenarioStream(data_dir, scenario, tuple(features), batch_size=batch_size)
            if verbose:
                print(f"B2 {scenario}: CV con finalistas C={finals}, "
                      f"máximo {b2_max_epochs} épocas", flush=True)
            b2_cv = b2_group_cv(
                stream, features, c_values=finals, n_splits=5, seed=seed,
                max_iter=b2_max_epochs, cache_dir="/content", output_dir=b2_dir,
                eta0=b2_eta0, tolerance=b2_gradient_tol, verbose=verbose,
            )
            if verbose:
                print(f"B2 {scenario}: CV terminada; resumiendo pliegues", flush=True)
            b2_summary, _ = summarize_b2_cv(b2_cv)
            atomic_csv(b2_summary.to_dict("records"), b2_dir / "b2_cv_summary.csv")
            if verbose:
                print(f"B2 {scenario}: reajustando C={finals} con todo train para evaluar val",
                      flush=True)
            b2_val = fit_b2_candidates_val(
                stream, features, finals, max_iter=b2_max_epochs, seed=seed,
                cache_dir="/content", output_dir=b2_dir, eta0=b2_eta0,
                tolerance=b2_gradient_tol, verbose=verbose,
            )
            del b2_cv, b2_summary, b2_val, stream
            gc.collect()

        run_phase(f"B2/{scenario}", b2_config, run_b2_scenario)
        outputs[f"b2_{scenario}"] = b2_dir
        if verbose and status[f"B2/{scenario}"]["state"] == "complete":
            print(f"B2 {scenario}: completo en {b2_dir}", flush=True)

    for scenario in ("A", "B", "C"):
        b3_dir = checkpoint_root / "b3" / "full" / f"escenario_{scenario}"
        b3_config = {"scenario": scenario, "features_sha256": stable_digest(list(features)),
                     "trials_per_study": b3_trials, "n_jobs": b3_n_jobs,
                     "max_ram_gib": max_ram_gib, "folds": 5, "seed": seed}

        def run_b3_scenario():
            stream = ScenarioStream(data_dir, scenario, tuple(features), batch_size=batch_size)
            if verbose:
                print(f"B3 {scenario}: iniciando Optuna "
                      f"({b3_trials} trials por métrica/modelo)", flush=True)
            b3_cv, b3_candidates = b3_optuna_cv(
                stream, features, n_splits=5, n_trials=b3_trials,
                max_train_games=None, seed=seed, n_jobs=b3_n_jobs,
                max_ram_gib=max_ram_gib, cache_dir="/content", output_dir=b3_dir,
                verbose=verbose,
            )
            atomic_csv(b3_candidates.to_dict("records"), b3_dir / "b3_candidatas.csv")
            b3_val = fit_b3_candidates_val(
                stream, features, b3_candidates, max_train_games=None, seed=seed,
                n_jobs=b3_n_jobs, max_ram_gib=max_ram_gib, cache_dir="/content",
                output_dir=b3_dir, verbose=verbose,
            )
            del b3_cv, b3_candidates, b3_val, stream
            gc.collect()

        run_phase(f"B3/{scenario}", b3_config, run_b3_scenario)
        outputs[f"b3_{scenario}"] = b3_dir
        if verbose and status[f"B3/{scenario}"]["state"] == "complete":
            print(f"B3 {scenario}: completo en {b3_dir}", flush=True)

    for scenario in ("A", "B", "C"):
        b4_dir = checkpoint_root / "b4" / "full" / f"escenario_{scenario}"
        b4_config = {"scenario": scenario, "features_sha256": stable_digest(list(features)),
                     "trials_per_study": b4_trials, "max_iter": b4_max_iter,
                     "patience": b4_patience, "max_ram_gib": max_ram_gib,
                     "folds": 5, "seed": seed}

        def run_b4_scenario():
            if verbose:
                print(f"B4 {scenario}: preparando datos; luego inicia Optuna "
                      f"({b4_trials} trials por métrica)", flush=True)
            with TemporaryDirectory(prefix=f"b4-{scenario}-", dir="/content") as cache:
                stream = ScenarioStream(data_dir, scenario, tuple(features), batch_size=batch_size)
                train = materialize_split(stream, features, "train", cache)
                val = materialize_split(stream, features, "val", cache)
                try:
                    b4_cv, b4_candidates = b4_optuna_cv(
                        train, n_splits=5, n_trials=b4_trials, seed=seed,
                        max_iter=b4_max_iter, patience=b4_patience,
                        max_ram_gib=max_ram_gib, output_dir=b4_dir, verbose=verbose,
                    )
                    atomic_csv(b4_candidates.to_dict("records"), b4_dir / "b4_candidatas.csv")
                    b4_val = fit_b4_candidates_val(
                        train, val, b4_candidates, seed=seed, max_iter=b4_max_iter,
                        patience=b4_patience, max_ram_gib=max_ram_gib,
                        output_dir=b4_dir, scenario=scenario, verbose=verbose,
                    )
                    del b4_cv, b4_candidates, b4_val
                finally:
                    train.close()
                    val.close()

        run_phase(f"B4/{scenario}", b4_config, run_b4_scenario)
        outputs[f"b4_{scenario}"] = b4_dir
        if verbose and status[f"B4/{scenario}"]["state"] == "complete":
            print(f"B4 {scenario}: completo en {b4_dir}", flush=True)

    if verbose:
        print("Pipeline completo: B2 finalistas → B3 → B4.", flush=True)
    return outputs
