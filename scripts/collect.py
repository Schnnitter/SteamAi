#!/usr/bin/env python3
"""Частый сбор Skinport. Пишет снимок в data/raw/YYYY-MM-DD/skinport-HHMM.json.gz."""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import time

from common import date_str, day_raw_dir, fetch_skinport_history, fetch_skinport_items, time_str


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--currency", default="EUR")
    ap.add_argument("--app-id", type=int, default=730)
    args = ap.parse_args()

    day = date_str()
    stamp = time_str()
    out_dir = day_raw_dir(day)

    items_resp = fetch_skinport_items(currency=args.currency, app_id=args.app_id)
    time.sleep(1)
    hist_resp = fetch_skinport_history()

    snapshot = {
        "ts": stamp,
        "day": day,
        "currency": args.currency,
        "app_id": args.app_id,
        "items": {
            "status": items_resp.status_code,
            "data": items_resp.json() if items_resp.status_code == 200 else None,
        },
        "history": {
            "status": hist_resp.status_code,
            "data": hist_resp.json() if hist_resp.status_code == 200 else None,
        },
    }

    out = out_dir / f"skinport-{stamp}.json.gz"
    with gzip.open(out, "wt", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False)

    n_items = len(snapshot["items"]["data"] or []) if snapshot["items"]["data"] else 0
    n_hist = len(snapshot["history"]["data"] or []) if snapshot["history"]["data"] else 0
    mb = out.stat().st_size / 1024 / 1024
    print(f"[{day} {stamp}] items={items_resp.status_code}/{n_items} "
          f"history={hist_resp.status_code}/{n_hist} -> {out.name} ({mb:.2f} MB)")

    return 0 if items_resp.status_code == 200 else 1


if __name__ == "__main__":
    sys.exit(main())