# Покрытие источников

| Источник | Среда | Игры | Поля | Квота | Ограничения | Дата | Код | Записей | Вердикт |
|---|---|---|---|---|---|---|---|---|---|
| Skinport /v1/items | дом | CS2 | market_hash_name, min_price, max_price, mean_price, quantity | 8 / 5 мин | требует Accept-Encoding: br; min_price=null = нет в продаже | | | | |
| Skinport /v1/sales/history | дом | CS2 | агрегаты 24ч/7д/30д/90д | 8 / 5 мин | требует Accept-Encoding: br | | | | |
| Steam /market/priceoverview | дом | CS2 и др. | lowest_price, median_price, volume | офиц. нет | 1 запрос / 3-4 сек, 429 до часов | | | | |
| Steam /inventory | дом | CS2 | assets | офиц. нет | только публичные инвентари | | | | |

## Известные пробелы

- Не проверено: Skinport из Codespaces и GitHub Actions.
- Не проверено: Steam с домашнего IP.