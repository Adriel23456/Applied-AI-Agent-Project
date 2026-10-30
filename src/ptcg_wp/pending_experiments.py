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


# Maximo de categorias por columna que acepta HistGradientBoostingClassifier (max_bins=255).
H2_CATEGORIAS_POR_BLOQUE = 255


def vocabulario_ids(valores):
    """Vocabulario de ids aprendido SOLO con train: ordenado por frecuencia (mayor primero) y,
    en empate, por id. Incluye el valor centinela de 'sin Pokemon activo' como una categoria
    mas. El orden solo decide en que bloque cae cada id; no cambia la informacion."""
    valores = np.asarray(valores, dtype=np.float64)
    valores = valores[np.isfinite(valores)]
    ids, cuentas = np.unique(valores, return_counts=True)
    orden = np.lexsort((ids, -cuentas))
    return ids[orden]


def codificar_ids_por_bloques(valores, vocabulario, por_bloque=H2_CATEGORIAS_POR_BLOQUE):
    """Codificacion SIN PERDIDA de un id con mas categorias de las que admite HGB.

    El vocabulario (todas las categorias de train) se reparte en bloques de 'por_bloque' ids
    y cada bloque es una columna categorica: el id ocupa su codigo en SU bloque y NaN (ausente)
    en los demas. Es biyectiva: cada id de train tiene una combinacion unica, asi que el arbol
    ve las 359 categorias completas con divisiones categoricas nativas. Un id que no aparece
    en train queda NaN en todos los bloques (categoria desconocida).
    Devuelve una matriz float32 de forma (n, numero_de_bloques)."""
    valores = np.asarray(valores, dtype=np.float64)
    vocabulario = np.asarray(vocabulario, dtype=np.float64)
    bloques = max(1, int(np.ceil(len(vocabulario) / por_bloque)))
    orden = np.argsort(vocabulario, kind='stable')
    ordenado = vocabulario[orden]
    pos = np.searchsorted(ordenado, valores)
    pos_segura = np.minimum(pos, len(ordenado) - 1)
    conocido = np.isfinite(valores) & (pos < len(ordenado)) & (ordenado[pos_segura] == valores)
    rango = np.where(conocido, orden[pos_segura], -1)
    salida = np.full((len(valores), bloques), np.nan, dtype=np.float32)
    for b in range(bloques):
        en_bloque = conocido & (rango // por_bloque == b)
        salida[en_bloque, b] = rango[en_bloque] % por_bloque
    return salida


def run_h2(data_dir, scenario, output_dir, seed=2026, cache_dir='/content'):
    """H2: B4 restringido a cuatro entradas (turno, primer jugador y los dos ids activos).

    Mismos hiperparametros y protocolo que B4 final (trial 20, vigilancia agrupada del 15 %,
    paciencia 30, tope 4000, pesos 1/n por partida, train propio y val del escenario). Los ids
    usan TODAS sus categorias de train mediante codificar_ids_por_bloques, porque HGB limita
    cada columna categorica a 255 valores. Las cuatro entradas no cambian: solo su forma.
    """
    _require_external_validation()
    features = ['game_turn', 'first_player_is_me', 'own_active_card', 'opp_active_card']
    ids = features[2:]
    root = Path(output_dir); root.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    stream = ScenarioStream(Path(data_dir), scenario, tuple(features))
    with TemporaryDirectory(prefix='h2-', dir=cache_dir) as tmp:
        train = materialize_split(stream, features, 'train', tmp)
        val = materialize_split(stream, features, 'val', tmp)
        try:
            _memory_guard(train, 10.0); _memory_guard(val, 10.0)
            x_train_4 = np.asarray(train.x); x_val_4 = np.asarray(val.x)
            vocabularios, columnas, mascara = {}, ['game_turn', 'first_player_is_me'], [False, False]
            partes_train, partes_val = [x_train_4[:, :2]], [x_val_4[:, :2]]
            codificacion = {}
            for nombre in ids:
                col = features.index(nombre)
                vocabulario = vocabulario_ids(x_train_4[:, col])
                vocabularios[nombre] = vocabulario.tolist()
                bloque_train = codificar_ids_por_bloques(x_train_4[:, col], vocabulario)
                bloque_val = codificar_ids_por_bloques(x_val_4[:, col], vocabulario)
                partes_train.append(bloque_train); partes_val.append(bloque_val)
                n_bloques = bloque_train.shape[1]
                columnas += [f'{nombre}_bloque{b}' for b in range(n_bloques)]
                mascara += [True] * n_bloques
                desconocido_val = ~np.isin(x_val_4[:, col], vocabulario)
                codificacion[nombre] = {'categorias_train': len(vocabulario), 'bloques': n_bloques,
                                        'fraccion_estados_val_desconocidos': float(desconocido_val.mean())}
            x_train = np.hstack(partes_train).astype(np.float32)
            x_val = np.hstack(partes_val).astype(np.float32)
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
                categorical_features=mascara)
            monitor.fit(x_train[fit], y[fit], sample_weight=_weights_for_codes(groups[fit]),
                        X_val=x_train[watch], y_val=y[watch], sample_weight_val=_weights_for_codes(groups[watch]))
            model = HistGradientBoostingClassifier(**params, max_iter=monitor.n_iter_, early_stopping=False,
                random_state=seed+1, categorical_features=mascara)
            model.fit(x_train, y, sample_weight=_weights_for_codes(groups))
            common = {'escenario': scenario, 'modelo': 'H2_restringido', 'semilla': seed,
                      'n_iter_vigilancia': int(monitor.n_iter_)}
            result = b4_metrics(np.asarray(val.y), model.predict_proba(x_val)[:, 1],
                                np.asarray(val.group), np.asarray(val.stage), common)
            pd.DataFrame(result).to_csv(root / 'h2_val.csv', index=False)
            joblib.dump({'model': model, 'features': features, 'columnas_modelo': columnas,
                         'vocabularios': vocabularios, 'categorias_por_bloque': H2_CATEGORIAS_POR_BLOQUE,
                         'version_sklearn': sklearn_version}, root / 'h2_restringido.joblib')
            config = {**common, 'features': features, 'columnas_modelo': columnas,
                      'codificacion_ids': 'bloques_categoricos_sin_perdida_v1',
                      'categorias_por_bloque': H2_CATEGORIAS_POR_BLOQUE, 'ids': codificacion,
                      'vocabularios': vocabularios, 'params': params,
                      'max_iter': 4000, 'patience': 30, 'monitor_fraction': .15,
                      'unknown_category': 'NaN en todos los bloques', 'sklearn_version': sklearn_version,
                      'seconds': time.perf_counter()-start}
            (root / 'h2_config.json').write_text(json.dumps(config, indent=2))
            print(f"H2 {scenario}: " + " | ".join(
                f"{n}: {c['categorias_train']} categorias en {c['bloques']} bloques, "
                f"{c['fraccion_estados_val_desconocidos']:.4f} de val desconocido"
                for n, c in codificacion.items()) + f" | arboles={monitor.n_iter_}", flush=True)
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

    def tabla(matrix):
        # LightGBM 4.6 + scikit-learn 1.7 avisan "X does not have valid feature names" si se
        # ajusta y predice con arreglos numpy. Con DataFrame y los nombres reales de las 62
        # columnas no hay aviso, las predicciones son identicas y el modelo guarda los nombres.
        return pd.DataFrame(np.asarray(matrix), columns=list(features))

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
        mdl.fit(tabla(x[fit]), np.asarray(y[fit]), sample_weight=_weights_for_codes(g[fit]),
                eval_set=[(tabla(x[watch]), np.asarray(y[watch]))], eval_metric='binary_logloss',
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
                    metrics = b4_metrics(np.asarray(train.y[ix]), mdl.predict_proba(tabla(train.x[ix]))[:, 1],
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
                    final.fit(tabla(train.x), np.asarray(train.y), sample_weight=_weights_for_codes(g))
                    common = {'escenario': scenario, 'modelo': 'LightGBM', 'trial': trial.number,
                              'n_iter_vigilancia': iterations, 'semilla': seed}
                    rows.extend(b4_metrics(np.asarray(val.y), final.predict_proba(tabla(val.x))[:, 1],
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
        # Nombres con que se ajusto LightGBM (los reales, o Column_i si se ajusto con numpy):
        # predecir con un DataFrame con esos mismos nombres evita el aviso de sklearn.
        candidate_names = [str(n) for n in getattr(candidate['model'], 'feature_names_in_', features)]
        yy, gg, stages, p_ref, p_cand = [], [], [], [], []
        for part in stream.iter_batches('val', columns=features):
            values = part.loc[:, features].to_numpy(dtype=np.float32)
            yy.append(part['y'].to_numpy(dtype=np.uint8)); gg.append(part['game_id'].to_numpy())
            stages.append(part['stage'].map({'inicio': 0, 'medio': 1, 'final': 2}).to_numpy(dtype=np.int8))
            p_ref.append(reference['model'].predict_proba(values)[:, 1])
            p_cand.append(candidate['model'].predict_proba(pd.DataFrame(values, columns=candidate_names))[:, 1])
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