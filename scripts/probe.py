#!/usr/bin/env python3
"""ШАГ 1: диагностика доступа к источникам."""
from __future__ import annotations

import argparse
import json
import sys
import time

from common import (
    HAS_BROTLI, RAW, SESSION, STEAMID_PUBLIC, STEAM_INVENTORY, STEAM_PRICE,
    fetch_skinport_history, fetch_skinport_items, local_now,
)


def _summary(r, source: str, url: str) -> dict:
    return {
        "ts": local_now().isoformat(timespec="seconds"),
        "source": source,
        "url": url,
        "status": r.status_code,
        "content_type": r.headers.get("Content-Type"),
        "content_encoding": r.headers.get("Content-Encoding"),
        "retry_after": r.headers.get("Retry-After"),
        "bytes": len(r.content or b""),
        "records": None,
        "samples": [],
        "error": None,
    }


def probe_skinport_items(currency: str = "EUR") -> dict:
    r = fetch_skinport_items(currency=currency)
    info = _summary(r, "skinport/items", "https://api.skinport.com/v1/items")
    try:
        data = r.json()
        if isinstance(data, list):
            info["records"] = len(data)
            info["samples"] = [d.get("market_hash_name") for d in data[:3] if isinstance(d, dict)]
    except Exception as e:
        info["error"] = type(e).__name__
    return info


def probe_skinport_history() -> dict:
    r = fetch_skinport_history()
    info = _summary(r, "skinport/sales-history", "https://api.skinport.com/v1/sales/history")
    try:
        data = r.json()
        if isinstance(data, list):
            info["records"] = len(data)
            info["samples"] = [d.get("market_hash_name") for d in data[:3] if isinstance(d, dict)]
    except Exception as e:
        info["error"] = type(e).__name__
    return info


def probe_steam_priceoverview(name: str = "AK-47 | Redline (Field-Tested)",
                              appid: int = 730, currency: int = 5) -> dict:
    r = SESSION.get(STEAM_PRICE,
                    params={"appid": appid, "market_hash_name": name, "currency": currency},
                    timeout=30)
    info = _summary(r, "steam/priceoverview", "https://steamcommunity.com/market/priceoverview/")
    try:
        data = r.json()
        info["records"] = 1 if data.get("success") else 0
        if data.get("lowest_price"):
            info["samples"] = [data["lowest_price"]]
    except Exception as e:
        info["error"] = type(e).__name__
    return info


def probe_steam_inventory(steamid: str) -> dict:
    url = STEAM_INVENTORY.format(steamid=steamid)
    r = SESSION.get(url, params={"count": 2000, "l": "english"}, timeout=30)
    info = _summary(r, "steam/inventory", "https://steamcommunity.com/inventory/<steamid>/730/2")
    try:
        data = r.json()
        info["records"] = len(data.get("assets") or [])
        info["samples"] = [a.get("classid") for a in (data.get("assets") or [])[:3]]
    except Exception as e:
        info["error"] = type(e).__name__
    return info


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, choices=[
        "skinport-items", "skinport-history",
        "steam-priceoverview", "steam-inventory", "all",
    ])
    ap.add_argument("--currency", default="EUR")
    args = ap.parse_args()

    if not HAS_BROTLI:
        print("WARN: пакет brotli не установлен.")

    results = []

    if args.source in ("skinport-items", "all"):
        results.append(probe_skinport_items(currency=args.currency))
        if args.source == "all":
            time.sleep(1)

    if args.source in ("skinport-history", "all"):
        if args.source == "all":
            time.sleep(1)
        results.append(probe_skinport_history())

    if args.source in ("steam-priceoverview", "all"):
        time.sleep(4)
        results.append(probe_steam_priceoverview())

    if args.source in ("steam-inventory", "all"):
        if not STEAMID_PUBLIC:
            print("SKIP steam/inventory: STEAMID_PUBLIC пуст в .env")
        else:
            time.sleep(4)
            results.append(probe_steam_inventory(STEAMID_PUBLIC))

    stamp = local_now().strftime("%Y-%m-%d-%H%M")
    out = RAW / f"probe-{stamp}.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    for r in results:
        print(f"{r['source']:24} status={r['status']} enc={r['content_encoding']} "
              f"records={r['records']} retry_after={r['retry_after']}")
        if r["samples"]:
            print(f"  samples: {r['samples']}")
        if r["error"]:
            print(f"  error: {r['error']}")

    print(f"\nСохранено: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())