"""H2: B4 restringido a cuatro entradas (turno, primer jugador y los dos ids activos).

H2 se refuta si este modelo iguala a B4 con el estado completo. Los ids conservan todas
sus categorias de train mediante una codificacion por bloques sin perdida.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import time

import joblib
import numpy as np
import pandas as pd
from sklearn import __version__ as sklearn_version
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupShuffleSplit

from ptcg_wp.b4 import (_memory_guard, _require_external_validation,
                        _weights_for_codes, materialize_split)
from ptcg_wp.data import ScenarioStream
from ptcg_wp.evaluation import metric_rows_codes


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
            result = metric_rows_codes(np.asarray(val.y), model.predict_proba(x_val)[:, 1],
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
