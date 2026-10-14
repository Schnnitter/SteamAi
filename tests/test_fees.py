"""Тесты расчёта комиссий. Все проверки сверены с официальной справкой Steam."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from fees import (
    steam_buyer_price, steam_seller_price,
    skinport_seller_price, skinport_buyer_price,
    breakeven_steam, breakeven_skinport, compare_paths,
)


def test_steam_example_from_help():
    """Справка Steam: продавец ставит 1.00 → покупатель видит 1.15."""
    assert steam_buyer_price(1.00) == 1.15
    assert steam_seller_price(1.15) == 1.00


def test_steam_min_fee():
    """На дешёвых предметах срабатывает минимум $0.01 на каждую часть."""
    # seller 0.03 → buyer = 0.03 + 0.01 + 0.01 = 0.05
    assert steam_buyer_price(0.03) == 0.05
    # обратно: buyer 0.05 → seller = 0.05 - 0.02 = 0.03
    assert steam_seller_price(0.05) == 0.03


def test_steam_big_price():
    """На дорогих предметах минимум не мешает."""
    assert steam_seller_price(115.00) == 100.00
    assert steam_seller_price(1150.00) == 1000.00


def test_steam_other_game():
    """Для игр без CS2-комиссии (5%) формула другая."""
    # app_id 999 (не в списке) → 5% Steam + 5% game = 10%
    # buyer 1.10 → seller 1.00
    assert steam_seller_price(1.10, app_id=999) == 1.00


def test_skinport_standard():
    """Skinport: 8% комиссии продавца."""
    assert skinport_seller_price(100.0) == 92.0
    assert skinport_buyer_price(92.0) == 100.0


def test_skinport_over_1000():
    """Свыше 1000 — комиссия 6%."""
    assert skinport_seller_price(1000.0) == 940.0


def test_breakeven_steam():
    """Купил за 120, хочу 125 → нужна цена покупателя около 143.75."""
    be = breakeven_steam(120.0, 125.0)
    assert be["buyer_price_needed"] == 143.75
    assert be["profit_target_pct"] == 4.17


def test_breakeven_skinport():
    """Skinport: чтобы получить 125, цена = 125/0.92 = 135.87."""
    be = breakeven_skinport(120.0, 125.0)
    assert be["buyer_price_needed"] == 135.87


def test_compare_paths():
    """Steam vs Skinport при одной цене."""
    c = compare_paths(100.0)
    # Steam: 100/1.15 = 86.96
    # Skinport: 100*0.92 = 92.00
    assert c["steam"]["seller_gets"] == 86.96
    assert c["skinport"]["seller_gets"] == 92.0
    assert c["best_by_amount"] == "skinport"
    assert c["difference"] == 5.04


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))