"""Поиск предмета в истории daily/*.csv и в свежих raw-снимках."""
from __future__ import annotations

import csv
import gzip
import json
from pathlib import Path
from typing import Optional

try:
    from rapidfuzz import fuzz, process
    HAS_FUZZ = True
except ImportError:
    HAS_FUZZ = False


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_daily(day: str) -> list[dict]:
    """Читает data/daily/YYYY-MM-DD.csv → список словарей."""
    path = DATA_DIR / "daily" / f"{day}.csv"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_all_history() -> dict[str, dict[str, dict]]:
    """Все daily/*.csv → {market_hash_name: {day: row}}."""
    result: dict[str, dict[str, dict]] = {}
    daily_dir = DATA_DIR / "daily"
    if not daily_dir.exists():
        return result
    for path in sorted(daily_dir.glob("*.csv")):
        day = path.stem
        for row in load_daily(day):
            name = row.get("market_hash_name")
            if not name:
                continue
            result.setdefault(name, {})[day] = row
    return result


def load_latest_raw(date: str) -> Optional[dict]:
    """Последний raw-снимок за день → {"ts":..., "items": {...}}."""
    day_dir = DATA_DIR / "raw" / date
    if not day_dir.exists():
        return None
    files = sorted(day_dir.glob("skinport-*.json.gz"))
    if not files:
        return None
    with gzip.open(files[-1], "rt", encoding="utf-8") as f:
        return json.load(f)


def find_item(query: str, top_n: int = 3, threshold: int = 60) -> list[tuple[str, int]]:
    """Нечёткий поиск предмета. Возвращает [(market_hash_name, score), ...]."""
    catalog = list(load_all_history().keys())
    if not catalog:
        raw_dir = DATA_DIR / "raw"
        if raw_dir.exists():
            for day in sorted(raw_dir.iterdir(), reverse=True):
                if day.is_dir():
                    snap = load_latest_raw(day.name)
                    if snap:
                        catalog = [
                            it["market_hash_name"]
                            for it in (snap.get("items", {}).get("data") or [])
                            if it.get("market_hash_name")
                        ]
                        break
    if not catalog:
        return []

    if HAS_FUZZ:
        # combined принимает **kwargs (rapidfuzz передаёт score_cutoff)
        def combined(a: str, b: str, **kwargs) -> float:
            s1 = fuzz.token_set_ratio(a, b)
            s2 = fuzz.WRatio(a, b)
            return min(s1, s2)

        hits = process.extract(query, catalog, scorer=combined, limit=top_n)
        return [(name, int(score)) for name, score, _ in hits if score >= threshold]

    q = query.lower()
    exact = [c for c in catalog if c.lower() == q]
    if exact:
        return [(exact[0], 100)]
    loose = [c for c in catalog if q in c.lower()][:top_n]
    return [(c, 80) for c in loose]