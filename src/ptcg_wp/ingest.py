import argparse
import json
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import yaml

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


def game_row(path, day):
    with open(path, encoding="utf-8") as f:
        g = json.load(f)
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


def build_games_table(raw_day_dir, day):
    rows, corruptos = [], []
    for p in sorted(Path(raw_day_dir).glob("*.json")):
        try:
            rows.append(game_row(p, day))
        except json.JSONDecodeError:
            corruptos.append(p.name)
    if corruptos:
        print(f"{day}: {len(corruptos)} archivos corruptos omitidos: {corruptos[:5]}")
    return pd.DataFrame(rows)


def ingest_day(day, raw_dir, out_dir, keep_raw=False):
    out_file = Path(out_dir) / f"partidas_{day}.parquet"
    if out_file.exists():
        print(f"{day}: ya existe, se omite")
        return out_file
    raw_day = download_day(day, raw_dir)
    df = build_games_table(raw_day, day)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_file, index=False)
    if not keep_raw:
        shutil.rmtree(raw_day)
    print(f"{day}: {len(df)} partidas -> {out_file}")
    return out_file


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