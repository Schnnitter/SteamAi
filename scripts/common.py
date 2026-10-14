"""Общие утилиты: пути, сессия requests, вызовы Skinport и Steam."""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

try:
    import brotli  # noqa: F401
    HAS_BROTLI = True
except ImportError:
    HAS_BROTLI = False

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
DAILY = DATA / "daily"
LOGS = DATA / "logs"
for _p in (DATA, RAW, DAILY, LOGS):
    _p.mkdir(parents=True, exist_ok=True)

UA = "SteamAi/0.1 (personal use, no automation of trading)"
SKINPORT_ITEMS = "https://api.skinport.com/v1/items"
SKINPORT_HISTORY = "https://api.skinport.com/v1/sales/history"
STEAM_PRICE = "https://steamcommunity.com/market/priceoverview/"
STEAM_INVENTORY = "https://steamcommunity.com/inventory/{steamid}/730/2"

STEAMID_PUBLIC = os.environ.get("STEAMID_PUBLIC", "").strip()

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA, "Accept-Encoding": "br"})


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def local_now() -> dt.datetime:
    return dt.datetime.now().astimezone()


def date_str(d: dt.datetime | None = None) -> str:
    return (d or local_now()).strftime("%Y-%m-%d")


def time_str(d: dt.datetime | None = None) -> str:
    return (d or local_now()).strftime("%H%M")


def day_raw_dir(day: str | None = None) -> Path:
    p = RAW / (day or date_str())
    p.mkdir(parents=True, exist_ok=True)
    return p


def fetch_skinport_items(currency: str = "EUR", app_id: int = 730,
                         tradable: int = 1, timeout: int = 30) -> requests.Response:
    return SESSION.get(
        SKINPORT_ITEMS,
        params={"app_id": app_id, "currency": currency, "tradable": tradable},
        timeout=timeout,
    )


def fetch_skinport_history(timeout: int = 30) -> requests.Response:
    return SESSION.get(SKINPORT_HISTORY, timeout=timeout)