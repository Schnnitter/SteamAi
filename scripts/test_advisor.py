"""Локальный прогон советника: на реальных данных и на выдуманных."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from advisor import advise, advise_from_index_item


def real_data_demo():
    path = ROOT / "data" / "index.json"
    if not path.exists():
        print("index.json не найден, пропускаю реальные данные")
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    print(f"Всего предметов: {data['count']}")
    print()
    print("Первые 10 — совет по реальным данным:")
    print(f"{'действие':<20} | {'уверенность':<8} | название")
    print("-" * 70)
    for it in data["items"][:10]:
        a = advise_from_index_item(it)
        print(f"{a.action:<20} | {a.confidence:<8} | {it['name'][:40]}")


def synthetic_demo():
    print()
    print("Выдуманные данные:")
    print(f"{'действие':<20} | {'уверенность':<8} | случай")
    print("-" * 70)

    cases = [
        ("растёт сильно + объём",   advise("X", 100.0, +3.5, 80, appearances=2)),
        ("падает сильно + объём",   advise("X", 100.0, -5.0, 60, appearances=2)),
        ("стабильно + объём",       advise("X", 100.0, +0.3, 100, appearances=2)),
        ("растёт, мало в продаже",  advise("X", 100.0, +3.5, 3, appearances=2)),
        ("дешёвый предмет",         advise("X", 0.5, +1.0, 50, appearances=2)),
        ("нет данных",              advise("X", None, None, None)),
        ("один снимок",             advise("X", 100.0, +3.0, 50, appearances=1)),
    ]
    for label, a in cases:
        print(f"{a.action:<20} | {a.confidence:<8} | {label}")
        for r in a.reasons:
            print(f"    • {r}")


if __name__ == "__main__":
    real_data_demo()
    synthetic_demo()