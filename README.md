# OI Screener (MVP)

Скринер “как coinglass/taoscalp” для поиска **роста открытого интереса (Open Interest)** по фьючерсам на нескольких биржах.

## Что уже сделано

- **Сетка “окон”**: в каждом окне отдельная биржа (сейчас: Binance USD‑M, Bybit Linear, OKX SWAP)
- Добавлены дополнительные биржи (best-effort, публичные API): Gate, Bitget, KuCoin Futures, MEXC, BingX, HTX, Hyperliquid
- **Сортировка** по изменению OI за выбранное окно (5m/1h/24h)
- **История** хранится в `sqlite` (для расчёта процентов)

## Что не удалось подключить (пока)

- **BitMart Futures**: публичные `contract/v1` эндпоинты возвращают “V1 deprecated”, а рабочие публичные пути **V2** в этой среде найти не удалось (все проверенные `contract/v2/...` возвращают 404).
- **LBank Futures**: по публичному домену `api.lbkex.com` фьючерсные/свап‑пути возвращают 404/HTML‑страницы (публичного OI API не обнаружено).
- **AsterDex**: домен отвечает страницей‑парковкой/таймаутом, публичного API OI не обнаружено.

## Запуск (Docker)

```bash
docker compose up --build
```

Открыть в браузере: `http://localhost:8000`

## Запуск (локально, Python)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## API

- `GET /api/exchanges` — список бирж
- `GET /api/oi?exchange=binance&sort_by=5m&order=desc&limit=50` — таблица OI с изменениями за 5m/1h/24h
- `GET /api/collector` — состояние сборщика

## Ограничения MVP

- Для снижения нагрузки берём **топ N контрактов по объёму** на бирже (по умолчанию `75`).
- Публичные эндпоинты у большинства бирж не дают “bulk open interest” — OI часто приходится запрашивать **по одному символу** (есть rate limits).
