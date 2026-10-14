#!/usr/bin/env python3
"""Вечерний отчёт: агрегат raw-снимков за день + покрытие + топ волатильности."""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
from pathlib import Path

from common import DAILY, LOGS, date_str, day_raw_dir


def _load_one(path: Path) -> dict | None:
    try:
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8") as f:
                return json.load(f)
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_snapshots(day: str) -> list[dict]:
    d = day_raw_dir(day)
    files = sorted(list(d.glob("skinport-*.json.gz")) + list(d.glob("skinport-*.json")))
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
    """Агрегат по market_hash_name. Одна запись = один уникальный предмет."""
    agg: dict[str, dict] = {}
    for s in snaps:
        data = (s.get("items") or {}).get("data") or []
        for row in data:
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
    only_one_snapshot = len(snaps) < 2
    for r in rows:
        if only_one_snapshot or r["appearances"] < 2:
            r["change_pct"] = None
            continue
        first, last = r.get("min_price_first"), r.get("min_price_last")
        if first and last and first > 0:
            r["change_pct"] = round((last - first) / first * 100, 2)
        else:
            r["change_pct"] = None
    return rows


def write_daily_csv(day: str, rows: list[dict]):
    out = DAILY / f"{day}.csv"
    fields = ["market_hash_name", "min_price_first", "min_price_last",
              "min_price_min", "min_price_max", "quantity_last",
              "appearances", "change_pct"]
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in fields})
    return out


def write_log(day: str, snaps: list[dict], rows: list[dict], gaps, window_h: int):
    out = LOGS / f"{day}.txt"
    stamps = sorted({s["ts"] for s in snaps if s.get("ts")})
    first = stamps[0] if stamps else "--"
    last = stamps[-1] if stamps else "--"
    total_min, _, _ = coverage_minutes(snaps)
    coverage_pct = round(total_min / (24 * 60) * 100, 1) if window_h else 0

    top = sorted(
        [r for r in rows if r.get("change_pct") is not None and r["appearances"] >= 2],
        key=lambda r: abs(r["change_pct"]), reverse=True,
    )[:3]
    null_count = sum(1 for r in rows if r.get("min_price_last") is None)

    items_status = snaps[-1]["items"]["status"] if snaps else "--"
    hist_status = snaps[-1]["history"]["status"] if snaps else "--"
    n_items = len((snaps[-1]["items"]["data"] or [])) if snaps else 0

    lines = [
        f"{day} | домашний сбор",
        f"Запусков за день: {len(snaps)}",
        f"Первый снимок: {first[:2]}:{first[2:]}",
        f"Последний снимок: {last[:2]}:{last[2:]}",
        f"Покрытие окна: {window_h} ч, суммарно {total_min} мин (~{coverage_pct}% суток)",
        f"Пропуски (>45 мин): {len(gaps)}",
    ]
    for a, b in gaps:
        lines.append(f"  {a[:2]}:{a[2:]} -> {b[:2]}:{b[2:]}")
    lines += [
        f"Skinport items: {items_status}, записей {n_items}",
        f"Skinport history: {hist_status}",
        f"Предметов с min_price=null: {null_count}",
        "Топ-3 по волатильности за день:",
    ]
    if top:
        for r in top:
            lines.append(f"  {r['market_hash_name']}: {r['change_pct']:+.2f}%")
    else:
        lines.append("  (нет данных — нужно минимум 2 снимка за день)")
    lines.append("Ошибки: нет" if not gaps else "Ошибки/пропуски: см. выше")

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", default=date_str())
    args = ap.parse_args()

    snaps = load_snapshots(args.day)
    if not snaps:
        print(f"[{args.day}] нет raw-снимков")
        return 1

    rows = aggregate_items(snaps)
    _, window_h, gaps = coverage_minutes(snaps)

    csv_path = write_daily_csv(args.day, rows)
    log_path = write_log(args.day, snaps, rows, gaps, window_h)

    print(f"[{args.day}] предметов: {len(rows)}, снимков: {len(snaps)}, пропусков: {len(gaps)}")
    print(f"CSV: {csv_path}")
    print(f"LOG: {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())