"""Парсер цен Steam. «2768,93 руб.» → 2768.93, «5₴» → 5.0, «$1.23» → 1.23."""
from __future__ import annotations

import re
from typing import Optional


# currency id → (символ, ISO код)
STEAM_CURRENCIES = {
    1:  ("$",    "USD"),
    2:  ("£",    "GBP"),
    3:  ("€",    "EUR"),
    5:  ("руб",  "RUB"),
    18: ("₴",    "UAH"),
    37: ("₸",    "KZT"),
}


def parse_price(s: Optional[str]) -> Optional[float]:
    """«2768,93 руб.» → 2768.93. Если распарсить нельзя — None."""
    if not s or not isinstance(s, str):
        return None

    # Убираем неразрывные пробелы
    cleaned = s.replace("\u00a0", " ").replace("\u202f", " ")

    # Оставляем только цифры, запятые, точки, дефисы
    cleaned = re.sub(r"[^\d,.\-]", "", cleaned)

    # Убираем точки и дефисы по краям (от «руб.», «грн.» и т.п.)
    cleaned = cleaned.strip(".-")

    if not cleaned or cleaned in ("-", ".", ","):
        return None

    # Если есть и точка, и запятая — определяем десятичный разделитель
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        after = len(cleaned) - cleaned.rfind(",") - 1
        if after in (1, 2):
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")

    try:
        return float(cleaned)
    except ValueError:
        return None


def detect_currency_id(s: str) -> Optional[int]:
    """По строке цены угадываем Steam currency id. «5₴» → 18, «$1.23» → 1."""
    if not s:
        return None
    for cid, (symbol, _iso) in STEAM_CURRENCIES.items():
        if symbol in s:
            return cid
    return None


def format_price(value: Optional[float], currency_id: int = 18) -> str:
    """Число → строка с символом валюты. 2768.93, 5 → «2768,93 ₴»."""
    if value is None:
        return "—"
    symbol = STEAM_CURRENCIES.get(currency_id, ("", "?"))[0]
    if currency_id in (5,):  # RUB пишется после числа
        return f"{value:.2f} {symbol}".replace(".", ",")
    return f"{symbol}{value:.2f}"