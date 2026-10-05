import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path

import pandas as pd
import yaml

from ptcg_wp.features import game_rows


SLUG = "kaggle/pokemon-tcg-ai-battle-episodes-{day}"


def load_days(config_path):
    with open(config_path, encoding="utf-8") as f:
        return [str(d) for d in yaml.safe_load(f)["dias"]]


def download_day(day, raw_dir):
    out = Path(raw_dir) / day
    marker = out / ".completo"
    if marker.exists():
        return out
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    subprocess.run(
        ["kaggle", "datasets", "download", "-d", SLUG.format(day=day),
         "-p", str(out), "--unzip"],
        check=True,
    )
    for z in out.glob("*.zip"):
        z.unlink()
    marker.touch()
    return out


def game_row(g, path, day):
    rewards = g.get("rewards") or [None, None]
    statuses = g.get("statuses") or [None, None]
    info = g.get("info") or {}
    agents = info.get("Agents") or [{}, {}]
    r0, r1 = rewards[0], rewards[1]
    if r0 is None or r1 is None or r0 == r1:
        winner = -1
    else:
        winner = 0 if r0 > r1 else 1
    return {
        "game_id": int(info.get("EpisodeId", Path(path).stem)),
        "day": day,
        "n_steps": len(g.get("steps", [])),
        "reward_0": r0,
        "reward_1": r1,
        "status_0": statuses[0],
        "status_1": statuses[1],
        "winner": winner,
        "agent_0": agents[0].get("Name"),
        "agent_1": agents[1].get("Name"),
    }


def build_tables(raw_day_dir, day):
    games, states, corruptos = [], [], []
    for p in sorted(Path(raw_day_dir).glob("*.json")):
        try:
            with open(p, encoding="utf-8") as f:
                g = json.load(f)
        except json.JSONDecodeError:
            corruptos.append(p.name)
            continue
        games.append(game_row(g, p, day))
        states.extend(game_rows(g, day))
    if corruptos:
        print(f"{day}: {len(corruptos)} archivos corruptos omitidos: {corruptos[:5]}")
    return pd.DataFrame(games), pd.DataFrame(states)


def ingest_day(day, raw_dir, out_dir, keep_raw=False):
    out_dir = Path(out_dir)
    games_file = out_dir / f"partidas_{day}.parquet"
    states_file = out_dir / f"estados_{day}.parquet"
    if games_file.exists() and states_file.exists():
        print(f"{day}: ya existe, se omite")
        return games_file, states_file
    t0 = time.time()
    raw_day = download_day(day, raw_dir)
    t1 = time.time()
    games, states = build_tables(raw_day, day)
    t2 = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)
    games.to_parquet(games_file, index=False)
    states.to_parquet(states_file, index=False)
    if not keep_raw:
        shutil.rmtree(raw_day)
    print(
        f"{day}: {len(games)} partidas, {len(states)} estados | "
        f"descarga {t1 - t0:.0f}s, procesamiento {t2 - t1:.0f}s"
    )
    return games_file, states_file

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/dias.yaml")
    ap.add_argument("--raw", default="/content/raw")
    ap.add_argument("--out", default="/content/datos")
    ap.add_argument("--keep-raw", action="store_true")
    args = ap.parse_args()
    for day in load_days(args.config):
        ingest_day(day, args.raw, args.out, args.keep_raw)


if __name__ == "__main__":
    main()