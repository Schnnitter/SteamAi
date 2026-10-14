# SteamAi — сборщик и советник

## Шаг 1. Проверка доступа

    run_probe.bat

Сделает по одному запросу к Skinport items, Skinport history, Steam priceoverview,
Steam inventory (по STEAMID_PUBLIC из .env).
Пишет результат в data\raw\probe-<дата-время>.json.

## Шаг 2. Сбор данных

    run_collect.bat

Пишет снимки в data\raw\YYYY-MM-DD\skinport-HHMM.json.

    run_daily.bat

Агрегирует в data\daily\YYYY-MM-DD.csv, лог в data\logs\YYYY-MM-DD.txt.

## Правила

- Steam: только по запросу, 1 запрос / 3-4 сек, кэш 30-60 мин.
- Skinport: 8 запросов / 5 мин, нам нужно 2 на снимок.
- Пропуски не интерполируем.
- min_price = null = нет в продаже, не 0.
- Никаких прокси.