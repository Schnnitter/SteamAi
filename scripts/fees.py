"""Расчёт комиссий Steam и Skinport. Все формулы — по официальной справке."""
from __future__ import annotations


# ═══════════════════════════════════════════════════════════════
# STEAM COMMUNITY MARKET
# ═══════════════════════════════════════════════════════════════
# Правила Valve:
# - Покупатель платит: цена_продавца + 5% Steam Fee + комиссия игры
# - Минимум $0.01 на каждую часть (Steam Fee и Game Fee)
# - Комиссия игры: CS2, Dota 2, Rust, TF2 = 10%; другие игры = 5%
# - Продавец получает цену_продавца
# - Пример из справки: продавец ставит 1.00 → покупатель видит 1.15

STEAM_BASE_FEE = 0.05

STEAM_GAME_FEE = {
    730:    0.10,   # CS2
    570:    0.10,   # Dota 2
    440:    0.10,   # TF2
    252490: 0.10,   # Rust
    753:    0.10,   # Steam Community (карточки, эмодзи, фоны)
}

STEAM_DEFAULT_GAME_FEE = 0.05
STEAM_MIN_FEE = 0.01

# Человекочитаемые названия игр
GAME_NAMES = {
    730:    "CS2",
    570:    "Dota 2",
    440:    "TF2",
    252490: "Rust",
    753:    "Steam Community",
}


def game_name(app_id: int) -> str:
    return GAME_NAMES.get(app_id, f"app_id={app_id}")


def steam_buyer_price(seller_price: float, app_id: int = 730) -> float:
    """Сколько заплатит покупатель, если продавец выставит seller_price."""
    game_fee = STEAM_GAME_FEE.get(app_id, STEAM_DEFAULT_GAME_FEE)
    steam_fee = max(seller_price * STEAM_BASE_FEE, STEAM_MIN_FEE)
    game_part = max(seller_price * game_fee, STEAM_MIN_FEE)
    return round(seller_price + steam_fee + game_part, 2)


def steam_seller_price(buyer_price: float, app_id: int = 730) -> float:
    """Сколько получит продавец, если покупатель заплатил buyer_price."""
    game_fee = STEAM_GAME_FEE.get(app_id, STEAM_DEFAULT_GAME_FEE)
    total_fee = STEAM_BASE_FEE + game_fee

    seller = buyer_price / (1 + total_fee)

    base_part = seller * STEAM_BASE_FEE
    game_part = seller * game_fee

    if base_part >= STEAM_MIN_FEE and game_part >= STEAM_MIN_FEE:
        return round(seller, 2)

    return round(buyer_price - 2 * STEAM_MIN_FEE, 2)


# ═══════════════════════════════════════════════════════════════
# SKINPORT
# ═══════════════════════════════════════════════════════════════
# Правила Skinport (проверить на skinport.com):
# - Продавец: 8% комиссии (6% от 1000 EUR, 2% для private listings)
# - Покупатель: ничего сверху не платит

SKINPORT_FEE = 0.08
SKINPORT_FEE_OVER_1000 = 0.06
SKINPORT_FEE_PRIVATE = 0.02
SKINPORT_THRESHOLD = 1000.0


def skinport_seller_price(buyer_price: float, private: bool = False,
                          currency_threshold: float = SKINPORT_THRESHOLD) -> float:
    """Сколько получит продавец, если покупатель заплатил buyer_price."""
    if private:
        fee = SKINPORT_FEE_PRIVATE
    elif buyer_price >= currency_threshold:
        fee = SKINPORT_FEE_OVER_1000
    else:
        fee = SKINPORT_FEE
    return round(buyer_price * (1 - fee), 2)


def skinport_buyer_price(seller_price: float, private: bool = False) -> float:
    """Какую цену надо поставить, чтобы получить seller_price на руки."""
    if private:
        fee = SKINPORT_FEE_PRIVATE
    elif seller_price >= SKINPORT_THRESHOLD * (1 - SKINPORT_FEE_OVER_1000):
        fee = SKINPORT_FEE_OVER_1000
    else:
        fee = SKINPORT_FEE
    return round(seller_price / (1 - fee), 2)


# ═══════════════════════════════════════════════════════════════
# СРАВНЕНИЕ ДВУХ ПУТЕЙ
# ═══════════════════════════════════════════════════════════════

def compare_paths(buyer_price: float, app_id: int = 730) -> dict:
    """Сравнивает Steam и Skinport для одной и той же цены покупателя."""
    steam_seller = steam_seller_price(buyer_price, app_id)
    skinport_seller = skinport_seller_price(buyer_price)

    return {
        "buyer_price": buyer_price,
        "app_id": app_id,
        "game": game_name(app_id),
        "steam": {
            "seller_gets": steam_seller,
            "note": "деньги на кошелёк Steam, наличными не выводятся",
        },
        "skinport": {
            "seller_gets": skinport_seller,
            "note": "вывод банком, нужна верификация личности",
        },
        "best_by_amount": "steam" if steam_seller > skinport_seller else "skinport",
        "difference": round(abs(steam_seller - skinport_seller), 2),
    }


# ═══════════════════════════════════════════════════════════════
# ТОЧКА БЕЗУБЫТОЧНОСТИ
# ═══════════════════════════════════════════════════════════════

def breakeven_steam(bought_for: float, target: float, app_id: int = 730) -> dict:
    """Сколько должен стоить предмет, чтобы вернуть target, купив за bought_for."""
    game_fee = STEAM_GAME_FEE.get(app_id, STEAM_DEFAULT_GAME_FEE)
    buyer_needed = round(target * (1 + STEAM_BASE_FEE + game_fee), 2)

    growth_pct = round((target - bought_for) / bought_for * 100, 2) if bought_for > 0 else None
    price_growth_pct = round((buyer_needed - bought_for) / bought_for * 100, 2) if bought_for > 0 else None

    return {
        "bought_for": bought_for,
        "target": target,
        "app_id": app_id,
        "game": game_name(app_id),
        "buyer_price_needed": buyer_needed,
        "profit_target_pct": growth_pct,
        "price_growth_needed_pct": price_growth_pct,
        "note": "без учёта курса валют и вывода денег",
    }


def breakeven_skinport(bought_for: float, target: float) -> dict:
    """То же для Skinport."""
    fee = SKINPORT_FEE_OVER_1000 if target >= SKINPORT_THRESHOLD else SKINPORT_FEE
    buyer_needed = round(target / (1 - fee), 2)

    growth_pct = round((target - bought_for) / bought_for * 100, 2) if bought_for > 0 else None
    price_growth_pct = round((buyer_needed - bought_for) / bought_for * 100, 2) if bought_for > 0 else None

    return {
        "bought_for": bought_for,
        "target": target,
        "buyer_price_needed": buyer_needed,
        "profit_target_pct": growth_pct,
        "price_growth_needed_pct": price_growth_pct,
        "note": "без учёта вывода денег и курса",
    }