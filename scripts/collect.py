#!/usr/bin/env python3
"""Сбор Skinport по всем играм. Пишет снимок в data/raw/YYYY-MM-DD/<game>-HHMM.json.gz."""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import time

from common import date_str, day_raw_dir, fetch_skinport_history, fetch_skinport_items, time_str

# Игры и их app_id
GAMES = {
    "cs2":   730,
    "dota2": 570,
    "tf2":   440,
    "rust":  252490,
}


def collect_game(game: str, app_id: int, currency: str) -> dict:
    items_resp = fetch_skinport_items(currency=currency, app_id=app_id)
    time.sleep(1)
    hist_resp = fetch_skinport_history()

    return {
        "game": game,
        "app_id": app_id,
        "items": {
            "status": items_resp.status_code,
            "data": items_resp.json() if items_resp.status_code == 200 else None,
        },
        "history": {
            "status": hist_resp.status_code,
            "data": hist_resp.json() if hist_resp.status_code == 200 else None,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--currency", default="EUR")
    ap.add_argument("--game", default="all",
                    help="cs2 | dota2 | tf2 | rust | all")
    args = ap.parse_args()

    day = date_str()
    stamp = time_str()
    out_dir = day_raw_dir(day)

    games = GAMES if args.game == "all" else {args.game: GAMES[args.game]}

    results = []
    for game, app_id in games.items():
        snap = collect_game(game, app_id, args.currency)
        snap["ts"] = stamp
        snap["day"] = day
        snap["currency"] = args.currency

        out = out_dir / f"{game}-{stamp}.json.gz"
        with gzip.open(out, "wt", encoding="utf-8") as f:
            json.dump(snap, f, ensure_ascii=False)

        n_items = len(snap["items"]["data"] or []) if snap["items"]["data"] else 0
        mb = out.stat().st_size / 1024 / 1024
        print(f"[{day} {stamp}] {game:6} items={snap['items']['status']}/{n_items} "
              f"history={snap['history']['status']} -> {out.name} ({mb:.2f} MB)")

        results.append(snap["items"]["status"] == 200)

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())