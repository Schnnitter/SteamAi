#!/usr/bin/env python3
"""Вечерний отчёт по всем играм: агрегат raw-снимков за день + покрытие."""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
from pathlib import Path

from common import DAILY, LOGS, date_str, day_raw_dir

GAMES = ["cs2", "dota2", "tf2", "rust"]


def _load_one(path: Path) -> dict | None:
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def load_snapshots(day: str, game: str) -> list[dict]:
    d = day_raw_dir(day)
    files = sorted(d.glob(f"{game}-*.json.gz"))
    snaps = []
    for f in files:
        s = _load_one(f)
        if s:
            snaps.append(s)
    return snaps


def coverage_minutes(snaps: list[dict]):
    stamps = sorted({s["ts"] for s in snaps if s.get("ts")})
    if len(stamps) < 2:
        return (0, 0, [])

    def to_min(t: str) -> int:
        return int(t[:2]) * 60 + int(t[2:])

    first, last = to_min(stamps[0]), to_min(stamps[-1])
    window_h = max(1, round((last - first) / 60))
    gaps = []
    for a, b in zip(stamps, stamps[1:]):
        if to_min(b) - to_min(a) > 45:
            gaps.append((a, b))
    return (last - first, window_h, gaps)


def aggregate_items(snaps: list[dict]) -> list[dict]:
    agg: dict[str, dict] = {}
    for s in snaps:
        for row in (s.get("items") or {}).get("data") or []:
            name = row.get("market_hash_name")
            if not name:
                continue
            rec = agg.setdefault(name, {
                "market_hash_name": name,
                "min_price_first": row.get("min_price"),
                "min_price_last": row.get("min_price"),
                "min_price_min": row.get("min_price"),
                "min_price_max": row.get("min_price"),
                "quantity_last": row.get("quantity"),
                "appearances": 0,
            })
            mp = row.get("min_price")
            if mp is not None:
                if rec["min_price_min"] is None or mp < rec["min_price_min"]:
                    rec["min_price_min"] = mp
                if rec["min_price_max"] is None or mp > rec["min_price_max"]:
                    rec["min_price_max"] = mp
                rec["min_price_last"] = mp
            rec["quantity_last"] = row.get("quantity")
            rec["appearances"] += 1

    rows = list(agg.values())
    one = len(snaps) < 2
    for r in rows:
        if one or r["appearances"] < 2:
            r["change_pct"] = None
            continue
        f, l = r["min_price_first"], r["min_price_last"]
        r["change_pct"] = round((l - f) / f * 100, 2) if f and l and f > 0 else None
    return rows


def write_daily_csv(day: str, rows: list[dict]):
    out = DAILY / f"{day}.csv"
    fields = ["game", "market_hash_name", "min_price_first", "min_price_last",
              "min_price_min", "min_price_max", "quantity_last",
              "appearances", "change_pct"]
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in fields})
    return out


def write_log(day: str, per_game: dict):
    out = LOGS / f"{day}.txt"
    lines = [f"{day} | cloud collect", ""]
    for game, info in per_game.items():
        lines.append(f"── {game.upper()} ──")
        lines.append(f"  snapshots: {info['snaps']}")
        lines.append(f"  items: {info['items']}")
        lines.append(f"  gaps: {len(info['gaps'])}")
        lines.append("")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", default=date_str())
    args = ap.parse_args()

    day = args.day
    all_rows = []
    per_game = {}

    for game in GAMES:
        snaps = load_snapshots(day, game)
        if not snaps:
            per_game[game] = {"snaps": 0, "items": 0, "gaps": []}
            continue

        rows = aggregate_items(snaps)
        for r in rows:
            r["game"] = game
        all_rows.extend(rows)

        _, _, gaps = coverage_minutes(snaps)
        per_game[game] = {"snaps": len(snaps), "items": len(rows), "gaps": gaps}

    if not all_rows:
        print(f"[{day}] нет raw-снимков")
        return 1

    csv_path = write_daily_csv(day, all_rows)
    log_path = write_log(day, per_game)

    total = sum(info["items"] for info in per_game.values())
    print(f"[{day}] всего предметов: {total}")
    for game, info in per_game.items():
        print(f"  {game:6} snapshots={info['snaps']} items={info['items']}")
    print(f"CSV: {csv_path}")
    print(f"LOG: {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())