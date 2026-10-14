"""Советник: на основе цены, изменения и количества выдаёт рекомендацию.

Правила прозрачные. Без ИИ. Все пороги настраиваются в константах внизу.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional


# ─── Пороги (меняй под себя) ───
CHANGE_UP_STRONG = 2.0       # % — рост, тренд вверх
CHANGE_DOWN_STRONG = -2.0    # % — падение, тренд вниз
LOW_LIQUIDITY_QTY = 5        # меньше предметов в продаже — мало данных
HIGH_LIQUIDITY_QTY = 50      # много — предмет ликвидный
MIN_PRICE_TO_SELL = 1.0      # EUR — ниже комиссии съедят
DISCREPANCY_PCT = 25.0       # % — большой разрыв между Steam и Skinport


@dataclass
class Advice:
    action: str          # "продавать" | "держать" | "ждать" | "мало данных" | "проверить вручную"
    confidence: str      # "высокая" | "средняя" | "низкая"
    reasons: list[str]
    numbers: dict

    def to_dict(self) -> dict:
        return asdict(self)


def advise(
    name: str,
    price: Optional[float],
    change_pct: Optional[float],
    quantity: Optional[int],
    appearances: int = 1,
    steam_seller_price: Optional[float] = None,
    skinport_seller_price: Optional[float] = None,
) -> Advice:
    """Возвращает рекомендацию с причинами."""
    reasons: list[str] = []
    numbers = {
        "price": price,
        "change_pct": change_pct,
        "quantity": quantity,
        "appearances": appearances,
    }

    # ─── Проверка базовых данных ───
    if price is None:
        return Advice(
            action="мало данных",
            confidence="низкая",
            reasons=["Нет цены в источнике."],
            numbers=numbers,
        )

    if appearances < 2 or change_pct is None:
        reasons.append(f"Снимков за день: {appearances}. Нужно минимум 2 для оценки динамики.")
        if quantity is None or quantity == 0:
            reasons.append("Нет данных о количестве в продаже.")
        return Advice(
            action="мало данных",
            confidence="низкая",
            reasons=reasons,
            numbers=numbers,
        )

    # ─── Низкая цена: комиссии съедят ───
    if price < MIN_PRICE_TO_SELL:
        reasons.append(f"Цена {price:.2f} EUR — комиссии площадок могут съесть всю выручку.")
        return Advice(
            action="не стоит продавать",
            confidence="средняя",
            reasons=reasons,
            numbers=numbers,
        )

    # ─── Разрыв между Steam и Skinport ───
    if steam_seller_price is not None and skinport_seller_price is not None:
        diff_pct = abs(steam_seller_price - skinport_seller_price) / max(price, 0.01) * 100
        numbers["steam_vs_skinport_pct"] = round(diff_pct, 2)
        if diff_pct > DISCREPANCY_PCT:
            reasons.append(
                f"Разрыв между Steam и Skinport: {diff_pct:.1f}%. "
                "Это подозрительно — проверь вручную."
            )
            return Advice(
                action="проверить вручную",
                confidence="низкая",
                reasons=reasons,
                numbers=numbers,
            )

    # ─── Ликвидность ───
    if quantity is None or quantity == 0:
        reasons.append("В продаже нет предложений (quantity=0). Цена ненадёжна.")
        return Advice(
            action="мало данных",
            confidence="низкая",
            reasons=reasons,
            numbers=numbers,
        )
    if quantity < LOW_LIQUIDITY_QTY:
        reasons.append(f"В продаже всего {quantity} шт. Ликвидность низкая — цена может быть случайной.")

    # ─── Логика по тренду ───
    # Растёт
    if change_pct >= CHANGE_UP_STRONG:
        reasons.append(f"Цена за день выросла на {change_pct:+.2f}%.")
        if quantity >= HIGH_LIQUIDITY_QTY:
            reasons.append(f"Объём высокий ({quantity} шт.) — тренд подтверждён.")
            return Advice(
                action="держать",
                confidence="средняя",
                reasons=reasons,
                numbers=numbers,
            )
        reasons.append(f"Объём умеренный ({quantity} шт.) — рост может быть случайным.")
        return Advice(
            action="держать",
            confidence="низкая",
            reasons=reasons,
            numbers=numbers,
        )

    # Падает
    if change_pct <= CHANGE_DOWN_STRONG:
        reasons.append(f"Цена за день упала на {change_pct:+.2f}%.")
        if quantity >= HIGH_LIQUIDITY_QTY:
            reasons.append(f"Объём высокий ({quantity} шт.) — тренд вниз подтверждён.")
            return Advice(
                action="продавать",
                confidence="средняя",
                reasons=reasons,
                numbers=numbers,
            )
        reasons.append(f"Объём умеренный ({quantity} шт.).")
        return Advice(
            action="продавать",
            confidence="низкая",
            reasons=reasons,
            numbers=numbers,
        )

    # Стабильно ±2%
    reasons.append(f"Цена за день почти не изменилась ({change_pct:+.2f}%).")
    if quantity >= HIGH_LIQUIDITY_QTY:
        reasons.append(f"Ликвидность высокая ({quantity} шт.).")
        return Advice(
            action="продавать сейчас",
            confidence="средняя",
            reasons=reasons,
            numbers=numbers,
        )
    reasons.append(f"Ликвидность низкая/средняя ({quantity} шт.). Можно подождать.")
    return Advice(
        action="ждать",
        confidence="низкая",
        reasons=reasons,
        numbers=numbers,
    )


def advise_from_index_item(item: dict) -> Advice:
    """Хелпер: совет прямо из записи index.json."""
    return advise(
        name=item.get("name", "?"),
        price=item.get("min_price"),
        change_pct=item.get("change_pct"),
        quantity=item.get("quantity"),
        appearances=2 if item.get("change_pct") is not None else 1,
    )