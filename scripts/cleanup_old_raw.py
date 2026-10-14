#!/usr/bin/env python3
"""Удаляет raw-снимки старше N дней. Daily CSV за эти дни уже созданы."""
from __future__ import annotations

import argparse
import datetime as dt
import sys

from common import RAW


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    args = ap.parse_args()

    cutoff = dt.date.today() - dt.timedelta(days=args.days)
    removed_files = 0
    removed_dirs = 0

    for day_dir in RAW.iterdir():
        if not day_dir.is_dir():
            continue
        try:
            d = dt.date.fromisoformat(day_dir.name)
        except ValueError:
            continue
        if d < cutoff:
            for f in day_dir.iterdir():
                if f.is_file():
                    f.unlink()
                    removed_files += 1
            try:
                day_dir.rmdir()
                removed_dirs += 1
            except OSError:
                pass

    print(f"cleanup: удалено {removed_files} файлов и {removed_dirs} папок старше {cutoff}")
    return 0


if __name__ == "__main__":
    sys.exit(main())