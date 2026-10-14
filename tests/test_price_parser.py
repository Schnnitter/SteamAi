"""Тесты парсера цен Steam."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from price_parser import parse_price, detect_currency_id, format_price


def test_rubles():
    assert parse_price("2768,93 руб.") == 2768.93
    assert parse_price("5,50 руб.") == 5.5
    assert parse_price("1234 руб.") == 1234.0


def test_uah():
    assert parse_price("5₴") == 5.0
    assert parse_price("1 234,56₴") == 1234.56


def test_usd():
    assert parse_price("$1.23") == 1.23
    assert parse_price("$1,234.56") == 1234.56


def test_eur():
    assert parse_price("12,34€") == 12.34
    assert parse_price("1.234,56€") == 1234.56


def test_thousands():
    assert parse_price("1,234.56") == 1234.56
    assert parse_price("1.234,56") == 1234.56


def test_invalid():
    assert parse_price("") is None
    assert parse_price(None) is None
    assert parse_price("бесплатно") is None
    assert parse_price("руб.") is None
    assert parse_price("-") is None


def test_detect_currency():
    assert detect_currency_id("5₴") == 18
    assert detect_currency_id("$1.23") == 1
    assert detect_currency_id("12,34€") == 3
    assert detect_currency_id("100 руб.") == 5
    assert detect_currency_id("abc") is None


def test_format():
    assert format_price(2768.93, currency_id=18) == "₴2768.93"
    assert format_price(None) == "—"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))