"""Генерирует index.json — компактный каталог для сайта (все игры)."""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

from item_lookup import DATA_DIR

GAMES = ["cs2", "dota2", "tf2", "rust"]


def latest_raw_day() -> str | None:
    raw = DATA_DIR / "raw"
    if not raw.exists():
        return None
    days = sorted([d.name for d in raw.iterdir() if d.is_dir()], reverse=True)
    return days[0] if days else None


def fnum(v):
    try:
        return float(v) if v not in (None, "", "None") else None
    except (ValueError, TypeError):
        return None


def load_latest_per_game(day: str) -> dict[str, dict]:
    """Для каждой игры берёт последний .gz снимок за день."""
    result = {}
    day_dir = DATA_DIR / "raw" / day
    if not day_dir.exists():
        return result
    for game in GAMES:
        files = sorted(day_dir.glob(f"{game}-*.json.gz"))
        if not files:
            continue
        try:
            with gzip.open(files[-1], "rt", encoding="utf-8") as f:
                result[game] = json.load(f)
        except Exception:
            pass
    return result


def load_daily_last_row_per_game() -> dict[str, dict[str, dict]]:
    """Из последнего daily CSV достаёт строку по каждому предмету."""
    daily = DATA_DIR / "daily"
    if not daily.exists():
        return {}
    files = sorted(daily.glob("*.csv"))
    if not files:
        return {}
    import csv
    result: dict[str, dict[str, dict]] = {}
    with files[-1].open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            game = row.get("game") or "cs2"
            name = row.get("market_hash_name")
            if name:
                result.setdefault(game, {})[name] = row
    return result


def build_index() -> dict:
    day = latest_raw_day()
    if not day:
        return {"generated": "unknown", "count": 0, "items": []}

    fresh = load_latest_per_game(day)
    daily_last = load_daily_last_row_per_game()

    items = []
    currency = "EUR"
    ts_global = None

    for game in GAMES:
        snap = fresh.get(game)
        if not snap:
            continue
        ts_global = snap.get("ts") or ts_global
        currency = snap.get("currency", "EUR")
        daily_rows = daily_last.get(game, {})

        for it in (snap.get("items") or {}).get("data") or []:
            name = it.get("market_hash_name")
            if not name:
                continue
            drow = daily_rows.get(name, {})
            items.append({
                "name": name,
                "game": game,
                "min_price": fnum(it.get("min_price")) or fnum(drow.get("min_price_last")),
                "max_price": fnum(it.get("max_price")) or fnum(drow.get("min_price_max")),
                "mean_price": fnum(it.get("mean_price")),
                "quantity": it.get("quantity"),
                "change_pct": fnum(drow.get("change_pct")),
                "day": day,
                "ts": snap.get("ts"),
            })

    items.sort(key=lambda x: (x["game"], x["name"]))

    return {
        "generated": day,
        "ts": ts_global,
        "currency": currency,
        "count": len(items),
        "items": items,
    }


def main() -> int:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR / "index.json"
    data = build_index()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    size_mb = out_path.stat().st_size / 1024 / 1024
    games_count = {}
    for it in data["items"]:
        games_count[it["game"]] = games_count.get(it["game"], 0) + 1
    print(f"index.json: {data['count']} items, {size_mb:.2f} MB -> {out_path}")
    for g, n in games_count.items():
        print(f"  {g}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())