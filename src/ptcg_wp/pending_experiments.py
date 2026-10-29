"""Experimentos pendientes de etapa 04; solo leen train y val."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import time

import joblib
import numpy as np
import pandas as pd
from sklearn import __version__ as sklearn_version
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupShuffleSplit, train_test_split

from ptcg_wp.baselines import ScenarioStream, weights_by_game
from ptcg_wp.model_comparison import paired_game_auc_bootstrap
from ptcg_wp.b2 import _collect_rows, _metric_rows, _pipeline, sample_train_games
from ptcg_wp.b4 import (materialize_split, fit_b4_candidates_val, _metric_rows as b4_metrics,
                        _weights_for_codes, _memory_guard, _require_external_validation)


def leakage_comparison(stream, features, output_dir, seed=2026, max_games=200, c_value=0.1):
    """Misma muestra de train y mismo ajuste LBFGS, con dos reglas de división."""
    start = time.perf_counter()
    games = sample_train_games(stream, max_games, seed)
    x, y, groups, stages = _collect_rows(stream, features, 'train', games)
    indices = np.arange(len(y))
    row_fit, row_eval = train_test_split(indices, test_size=0.2, random_state=seed, stratify=y)
    group_fit, group_eval = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
                                 .split(x, y, groups))
    rows, overlaps = [], []
    for name, fit, held in [('fila', row_fit, row_eval), ('partida', group_fit, group_eval)]:
        model = _pipeline(c_value, 300)
        w = weights_by_game(groups[fit])
        model.fit(x[fit], y[fit], scale__sample_weight=w, logit__sample_weight=w)
        common = {'escenario': stream.scenario, 'division': name, 'C': c_value, 'semilla': seed}
        rows.extend(_metric_rows(y[held], model.predict_proba(x[held])[:, 1],
                                 groups[held], stages[held], common))
        fit_games, held_games = np.unique(groups[fit]), np.unique(groups[held])
        overlap = np.intersect1d(fit_games, held_games)
        overlaps.append({**common, 'partidas_ajuste': len(fit_games), 'partidas_evaluacion': len(held_games),
                         'partidas_en_ambos_lados': len(overlap),
                         'fraccion_evaluacion_con_partida_vista': len(overlap) / len(held_games),
                         'n_iter': int(model.named_steps['logit'].n_iter_[0])})
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / 'metricas.csv', index=False)
    pd.DataFrame(overlaps).to_csv(out / 'solapamiento.csv', index=False)
    (out / 'config.json').write_text(json.dumps({'scenario': stream.scenario, 'seed': seed,
        'max_games': max_games, 'sample_games': len(np.unique(groups)), 'C': c_value,
        'max_iter': 300, 'held_fraction': 0.2, 'features': list(features),
        'sklearn_version': sklearn_version, 'seconds': time.perf_counter()-start}, indent=2))
    return pd.DataFrame(rows), pd.DataFrame(overlaps)


def feature_families(features):
    """Familias mutuamente excluyentes; los nombres se guardan con la corrida."""
    progress = {'game_turn', 'turn_action_count', 'energy_attached', 'retreated',
                'supporter_played', 'stadium_played', 'stadium_in_play', 'first_player_is_me'}
    families = {'progreso': [f for f in features if f in progress],
                'diferenciales': [f for f in features if f.startswith('diff_')]}
    families['recursos_tablero'] = [f for f in features if f not in progress and not f.startswith('diff_')]
    if any(not family for family in families.values()) or sum(map(len, families.values())) != len(features):
        raise ValueError('No se pudieron definir las tres familias de características')
    return families


def run_b4_ablation(data_dir, scenario, features, candidate, output_dir, seed=2026, cache_dir='/content'):
    """Tres variantes: elimina una familia y mantiene configuración y protocolo de B4."""
    families = feature_families(features)
    root = Path(output_dir); root.mkdir(parents=True, exist_ok=True)
    (root / 'familias.json').write_text(json.dumps(families, indent=2, ensure_ascii=False))
    for name, removed in families.items():
        selected = [f for f in features if f not in removed]
        out = root / f'sin_{name}'; start = time.perf_counter()
        stream = ScenarioStream(Path(data_dir), scenario, tuple(selected))
        with TemporaryDirectory(prefix='b4-ablation-', dir=cache_dir) as tmp:
            train = materialize_split(stream, selected, 'train', tmp)
            val = materialize_split(stream, selected, 'val', tmp)
            try:
                fit_b4_candidates_val(train, val, candidate, seed=seed, max_iter=4000, patience=30,
                                      monitor_fraction=0.15, max_ram_gib=10.0,
                                      output_dir=out, scenario=scenario, verbose=True)
            finally:
                train.close(); val.close()
        (out / 'duracion.json').write_text(json.dumps({'seconds': time.perf_counter()-start}, indent=2))


def run_h2(data_dir, scenario, output_dir, seed=2026, cache_dir='/content'):
    """Cuatro entradas; codifica los dos IDs como categorías aprendidas solo en train."""
    _require_external_validation()
    features = ['game_turn', 'first_player_is_me', 'own_active_card', 'opp_active_card']
    root = Path(output_dir); root.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    stream = ScenarioStream(Path(data_dir), scenario, tuple(features))
    with TemporaryDirectory(prefix='h2-', dir=cache_dir) as tmp:
        train = materialize_split(stream, features, 'train', tmp)
        val = materialize_split(stream, features, 'val', tmp)
        try:
            _memory_guard(train, 10.0); _memory_guard(val, 10.0)
            x_train = np.asarray(train.x).copy(); x_val = np.asarray(val.x).copy()
            categories = {}
            unseen_val = {}
            for col, name in [(2, features[2]), (3, features[3])]:
                known = np.unique(x_train[:, col])
                if not np.isfinite(known).all() or len(known) > 255:
                    raise ValueError(f'{name}: {len(known)} categorías; HGB admite máximo 255. '
                                     'Debe definirse otra codificación antes de continuar.')
                categories[name] = known.tolist()
                unseen_val[name] = float(np.mean(~np.isin(x_val[:, col], known)))
                for matrix in (x_train, x_val):
                    values = matrix[:, col].copy()
                    indices = np.searchsorted(known, values)
                    valid = (indices < len(known))
                    valid &= known[np.minimum(indices, len(known)-1)] == values
                    matrix[:, col] = np.where(valid, indices, np.nan)
            params = {'learning_rate': 0.06942837051487823, 'max_leaf_nodes': 31,
                      'min_samples_leaf': 50, 'l2_regularization': 4.250289335685325}
            groups = np.asarray(train.group)
            all_groups = np.arange(len(train.games), dtype=np.int32)
            fit_g, watch_g = next(GroupShuffleSplit(n_splits=1, test_size=.15, random_state=seed)
                                  .split(all_groups, groups=all_groups))
            fit = np.flatnonzero(np.isin(groups, all_groups[fit_g]))
            watch = np.flatnonzero(np.isin(groups, all_groups[watch_g]))
            y = np.asarray(train.y)
            monitor = HistGradientBoostingClassifier(**params, max_iter=4000, early_stopping=True,
                scoring='loss', n_iter_no_change=30, tol=1e-7, random_state=seed+1,
                categorical_features=[False, False, True, True])
            monitor.fit(x_train[fit], y[fit], sample_weight=_weights_for_codes(groups[fit]),
                        X_val=x_train[watch], y_val=y[watch], sample_weight_val=_weights_for_codes(groups[watch]))
            model = HistGradientBoostingClassifier(**params, max_iter=monitor.n_iter_, early_stopping=False,
                random_state=seed+1, categorical_features=[False, False, True, True])
            model.fit(x_train, y, sample_weight=_weights_for_codes(groups))
            common = {'escenario': scenario, 'modelo': 'H2_restringido', 'semilla': seed,
                      'n_iter_vigilancia': int(monitor.n_iter_)}
            result = b4_metrics(np.asarray(val.y), model.predict_proba(x_val)[:, 1],
                                np.asarray(val.group), np.asarray(val.stage), common)
            pd.DataFrame(result).to_csv(root / 'h2_val.csv', index=False)
            joblib.dump({'model': model, 'features': features, 'categories': categories,
                         'version_sklearn': sklearn_version}, root / 'h2_restringido.joblib')
            config = {**common, 'features': features, 'categories': categories, 'params': params,
                      'max_iter': 4000, 'patience': 30, 'monitor_fraction': .15,
                      'unknown_category': 'NaN', 'fraction_unknown_in_val': unseen_val, 'sklearn_version': sklearn_version,
                      'seconds': time.perf_counter()-start}
            (root / 'h2_config.json').write_text(json.dumps(config, indent=2))
        finally:
            train.close(); val.close()


def run_lightgbm(data_dir, features, output_dir, seed=2026, cache_dir='/content', n_jobs=2):
    """20 trials y 3 folds agrupados; una configuración elegida en CV antes de val."""
    import lightgbm as lgb
    import optuna
    from sklearn.model_selection import GroupKFold
    from ptcg_wp.checkpoints import stable_digest

    root = Path(output_dir); root.mkdir(parents=True, exist_ok=True)
    part = pd.read_parquet(Path(data_dir) / 'particiones.parquet')
    common_games = set(part.loc[(part.split_A == 'train') & (part.split_B == 'train') &
                                (part.split_C == 'train'), 'game_id'])
    stream_a = ScenarioStream(Path(data_dir), 'A', tuple(features))
    config = {'semilla': seed, 'trials': 20, 'folds': 3, 'monitor_fraction': .15,
              'max_iter_search': 2000, 'max_iter_final': 4000, 'patience': 30, 'features': list(features),
              'search_games_sha256': stable_digest(sorted(map(str, common_games))),
              'metric': 'log_loss', 'n_jobs': n_jobs,
              'search_space': {'learning_rate': [0.02, 0.2], 'num_leaves': [8, 16, 31],
                               'min_child_samples': [20, 50, 100], 'reg_lambda': [1e-6, 10.0]},
              'version_lightgbm': lgb.__version__,
              'version_optuna': optuna.__version__, 'protocol': 'lightgbm_b4_v1',
              'selection': 'max_cv_auc_then_min_log_loss_then_min_brier_then_trial',
              'comparison': 'paired_game_bootstrap_1000_95pct_auc_all_scenarios_and_no_observed_loss_brier_increase'}
    manifest = root / 'lightgbm_config.json'
    if manifest.exists() and json.loads(manifest.read_text()) != config:
        raise ValueError('La configuración difiere del estudio existente; usa otra carpeta.')
    manifest.write_text(json.dumps(config, indent=2))

    def model(params, iterations, model_seed=None):
        return lgb.LGBMClassifier(objective='binary', n_estimators=iterations,
            random_state=seed+1 if model_seed is None else model_seed, n_jobs=n_jobs, verbosity=-1, **params)

    def fit_monitor(data, group_codes, params, max_iter, monitor_seed=None, model_seed=None):
        split = GroupShuffleSplit(n_splits=1, test_size=.15, random_state=seed if monitor_seed is None else monitor_seed)
        a, b = next(split.split(group_codes, groups=group_codes))
        g = np.asarray(data.group)
        fit = np.flatnonzero(np.isin(g, group_codes[a])); watch = np.flatnonzero(np.isin(g, group_codes[b]))
        x, y = data.x, data.y
        mdl = model(params, max_iter, model_seed)
        mdl.fit(np.asarray(x[fit]), np.asarray(y[fit]), sample_weight=_weights_for_codes(g[fit]),
                eval_set=[(np.asarray(x[watch]), np.asarray(y[watch]))], eval_metric='binary_logloss',
                eval_sample_weight=[_weights_for_codes(g[watch])],
                callbacks=[lgb.early_stopping(30, verbose=False)])
        return mdl

    with TemporaryDirectory(prefix='lightgbm-search-', dir=cache_dir) as tmp:
        train = materialize_split(stream_a, features, 'train', tmp)
        try:
            _memory_guard(train, 10.0)
            search = np.array([i for i, game in enumerate(train.games) if game in common_games], dtype=np.int32)
            if len(search) < 6: raise ValueError('No hay suficientes partidas train comunes.')
            folds = list(GroupKFold(n_splits=3, shuffle=True, random_state=seed).split(search, groups=search))
            study = optuna.create_study(study_name='lightgbm_b4_v1',
                storage=f'sqlite:///{root / "lightgbm_optuna.sqlite3"}', load_if_exists=True,
                direction='minimize', sampler=optuna.samplers.TPESampler(seed=seed, n_startup_trials=5))
            for trial in study.get_trials(deepcopy=False, states=[optuna.trial.TrialState.RUNNING]):
                study.tell(trial.number, state=optuna.trial.TrialState.FAIL)
            def objective(trial):
                params = {'learning_rate': trial.suggest_float('learning_rate', .02, .2, log=True),
                          'num_leaves': trial.suggest_categorical('num_leaves', [8, 16, 31]),
                          'min_child_samples': trial.suggest_categorical('min_child_samples', [20, 50, 100]),
                          'reg_lambda': trial.suggest_float('reg_lambda', 1e-6, 10., log=True)}
                rows = []
                g = np.asarray(train.group)
                for fold, (fit, held) in enumerate(folds, start=1):
                    mdl = fit_monitor(train, search[fit], params, 2000, monitor_seed=seed+fold,
                                      model_seed=seed+trial.number*100+fold)
                    ix = np.flatnonzero(np.isin(g, search[held]))
                    metrics = b4_metrics(np.asarray(train.y[ix]), mdl.predict_proba(np.asarray(train.x[ix]))[:, 1],
                                         g[ix], np.asarray(train.stage[ix]), {'fold': fold}, include_stages=False)[0]
                    metrics['n_iter_vigilancia'] = int(mdl.best_iteration_)
                    rows.append(metrics)
                if not all(np.isfinite(row[m]) for row in rows for m in ('auc', 'log_loss', 'brier')):
                    raise ValueError('CV produjo métricas no finitas; revisar los datos antes de continuar.')
                for metric in ('auc', 'log_loss', 'brier'):
                    trial.set_user_attr(metric, float(np.mean([r[metric] for r in rows])))
                trial.set_user_attr('folds', rows)
                return trial.user_attrs['log_loss']
            complete = len(study.get_trials(deepcopy=False, states=[optuna.trial.TrialState.COMPLETE]))
            if complete < 20: study.optimize(objective, n_trials=20-complete)
            completed = study.get_trials(deepcopy=False, states=[optuna.trial.TrialState.COMPLETE])
            trials = pd.DataFrame([{'trial': t.number, **t.params, **{m: t.user_attrs[m] for m in ('auc','log_loss','brier')}} for t in completed])
            trials.to_csv(root / 'lightgbm_cv_trials.csv', index=False)
            pd.DataFrame([{'trial': t.number, **row} for t in completed for row in t.user_attrs['folds']]).to_csv(root / 'lightgbm_cv_folds.csv', index=False)
            # Una configuración compartida; se elige sin consultar val de ningún escenario.
            chosen = min(completed, key=lambda t: (-t.user_attrs['auc'], t.user_attrs['log_loss'],
                                                  t.user_attrs['brier'], t.number))
            candidates = [chosen]
            trials.loc[trials.trial.eq(chosen.number)].to_csv(root / 'lightgbm_finalista.csv', index=False)
        finally:
            train.close()
    for scenario in ('A', 'B', 'C'):
        stream = ScenarioStream(Path(data_dir), scenario, tuple(features))
        out = root / f'escenario_{scenario}'; out.mkdir(exist_ok=True)
        artifact = out / f'lightgbm_trial_{chosen.number}.joblib'
        report = out / 'lightgbm_val.csv'
        if artifact.exists() and report.exists():
            saved = pd.read_csv(report)
            if (len(saved) == 4 and set(saved['etapa']) == {'global', 'inicio', 'medio', 'final'}
                    and saved['trial'].eq(chosen.number).all()):
                print(f'LightGBM {scenario}: finalista y métricas ya guardadas; se omite el ajuste.', flush=True)
                continue
        with TemporaryDirectory(prefix='lightgbm-final-', dir=cache_dir) as tmp:
            train = materialize_split(stream, features, 'train', tmp)
            val = materialize_split(stream, features, 'val', tmp)
            try:
                _memory_guard(train, 10.0); _memory_guard(val, 10.0)
                g = np.asarray(train.group); all_groups = np.arange(len(train.games), dtype=np.int32)
                rows = []
                for trial in candidates:
                    monitor = fit_monitor(train, all_groups, trial.params, 4000)
                    iterations = int(monitor.best_iteration_)
                    final = model(trial.params, iterations)
                    final.fit(np.asarray(train.x), np.asarray(train.y), sample_weight=_weights_for_codes(g))
                    common = {'escenario': scenario, 'modelo': 'LightGBM', 'trial': trial.number,
                              'n_iter_vigilancia': iterations, 'semilla': seed}
                    rows.extend(b4_metrics(np.asarray(val.y), final.predict_proba(np.asarray(val.x))[:, 1],
                                           np.asarray(val.group), np.asarray(val.stage), common))
                    joblib.dump({'model': final, 'features': list(features), 'params': trial.params,
                                 'scenario': scenario, 'lightgbm_version': lgb.__version__},
                                out / f'lightgbm_trial_{trial.number}.joblib')
                pd.DataFrame(rows).to_csv(out / 'lightgbm_val.csv', index=False)
            finally:
                train.close(); val.close()


def compare_lightgbm_b4(data_dir, b4_root, lightgbm_root, seed=2026):
    """Decisión de selección sobre val; evalúa los tres escenarios por separado."""
    root = Path(lightgbm_root)
    chosen = pd.read_csv(root / 'lightgbm_finalista.csv')
    if len(chosen) != 1: raise ValueError('Se esperaba una sola configuración LightGBM seleccionada en CV.')
    trial = int(chosen.iloc[0]['trial'])
    output = root / 'comparacion_b4'; output.mkdir(exist_ok=True)
    metric_rows, decisions = [], []
    for scenario in ('A', 'B', 'C'):
        reference = joblib.load(Path(b4_root) / f'escenario_{scenario}' / 'b4_auc_CVtrial20.joblib')
        candidate = joblib.load(root / f'escenario_{scenario}' / f'lightgbm_trial_{trial}.joblib')
        features = reference['features']
        if features != candidate['features']:
            raise ValueError('B4 y LightGBM deben recibir las mismas características y en el mismo orden.')
        stream = ScenarioStream(Path(data_dir), scenario, tuple(features))
        yy, gg, stages, p_ref, p_cand = [], [], [], [], []
        for part in stream.iter_batches('val', columns=features):
            values = part.loc[:, features].to_numpy(dtype=np.float32)
            yy.append(part['y'].to_numpy(dtype=np.uint8)); gg.append(part['game_id'].to_numpy())
            stages.append(part['stage'].map({'inicio': 0, 'medio': 1, 'final': 2}).to_numpy(dtype=np.int8))
            p_ref.append(reference['model'].predict_proba(values)[:, 1])
            p_cand.append(candidate['model'].predict_proba(values)[:, 1])
        y = np.concatenate(yy); codes, _ = pd.factorize(np.concatenate(gg), sort=True)
        stage = np.concatenate(stages)
        ref_p, cand_p = np.clip(np.concatenate(p_ref), 1e-15, 1-1e-15), np.clip(np.concatenate(p_cand), 1e-15, 1-1e-15)
        ref_metrics = b4_metrics(y, ref_p, codes, stage, {'escenario': scenario, 'modelo': 'B4'})
        cand_metrics = b4_metrics(y, cand_p, codes, stage, {'escenario': scenario, 'modelo': 'LightGBM'})
        metric_rows.extend(ref_metrics + cand_metrics)
        ref, cand = ref_metrics[0], cand_metrics[0]
        interval, differences = paired_game_auc_bootstrap(y, ref_p, cand_p, codes, seed=seed)
        pd.DataFrame({'delta_auc': differences}).to_csv(output / f'bootstrap_auc_{scenario}.csv', index=False)
        delta_loss, delta_brier = cand['log_loss']-ref['log_loss'], cand['brier']-ref['brier']
        decisions.append({'escenario': scenario, 'delta_auc': cand['auc']-ref['auc'],
            'delta_log_loss': delta_loss, 'delta_brier': delta_brier, **interval,
            'cumple_regla': bool(interval['delta_auc_ci_lower'] > 0 and delta_loss <= 0 and delta_brier <= 0)})
        pd.DataFrame(metric_rows).to_csv(output / 'metricas_val.csv', index=False)
        pd.DataFrame(decisions).to_csv(output / 'comparacion_val.csv', index=False)
        print(f'LightGBM contra B4 {scenario}: {decisions[-1]}', flush=True)
    decision = {'decision': 'seleccionar_lightgbm' if all(r['cumple_regla'] for r in decisions) else 'mantener_b4',
        'rule': 'AUC CI95 lower>0 and observed delta_log_loss<=0 and delta_brier<=0 in A, B, C',
        'scope': 'seleccion_sobre_val; no es evaluacion_final_en_test', 'trial': trial,
        'n_boot': 1000, 'seed': seed, 'confidence': .95, 'interval': 'percentile',
        'limitations': 'No cuantifica incertidumbre de la búsqueda ni importancia práctica; '
                        'la ausencia de incremento observado en pérdidas no demuestra equivalencia.'}
    (output / 'decision_val.json').write_text(json.dumps(decision, indent=2, ensure_ascii=False))
    return pd.DataFrame(decisions), decision
