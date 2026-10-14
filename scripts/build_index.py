"""Генерирует index.json — компактный каталог для сайта."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from item_lookup import DATA_DIR, load_all_history, load_latest_raw


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


def build_index() -> dict:
    history = load_all_history()

    day = latest_raw_day()
    fresh: dict[str, dict] = {}
    ts = None
    currency = "EUR"
    if day:
        snap = load_latest_raw(day)
        if snap:
            ts = snap.get("ts")
            currency = snap.get("currency", "EUR")
            for it in (snap.get("items") or {}).get("data") or []:
                n = it.get("market_hash_name")
                if n:
                    fresh[n] = it

    items = []
    for name, days_map in history.items():
        last_day = max(days_map.keys())
        row = days_map[last_day]
        fresh_item = fresh.get(name, {})

        items.append({
            "name": name,
            "min_price": fnum(fresh_item.get("min_price")) or fnum(row.get("min_price_last")),
            "max_price": fnum(fresh_item.get("max_price")) or fnum(row.get("min_price_max")),
            "mean_price": fnum(fresh_item.get("mean_price")),
            "quantity": fresh_item.get("quantity"),
            "change_pct": fnum(row.get("change_pct")),
            "day": last_day,
            "ts": ts,
        })

    items.sort(key=lambda x: x["name"])

    return {
        "generated": day or "unknown",
        "ts": ts,
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
    print(f"index.json: {data['count']} items, {size_mb:.2f} MB -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())