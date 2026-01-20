# Open Interest Screener (Exchanges)

Скринер изменения **Open Interest** по списку тикеров, получающий данные **напрямую с бирж** (без Coinglass).

## Быстрый старт

1) Установить зависимости:

```bash
python -m pip install -e .
```

2) Ключи не нужны (используются публичные API бирж).

3) Запуск CLI-скринера:

```bash
coinglass-oi screen --symbols BTC,ETH,SOL --exchange OKX --interval 1h --limit 20
```

Сканировать **все фьючерсы** биржи (может быть долго):

```bash
coinglass-oi screen --all-futures --max-symbols 200 --exchange OKX --interval 1h --limit 20
```

4) Запуск HTTP API:

```bash
coinglass-oi serve --port 8000
```

5) Визуальный клиент (UI в браузере):

```bash
coinglass-oi ui --port 8501
```

Открыть в браузере: `http://localhost:8501`

Пример запроса:

```bash
curl "http://localhost:8000/screener?symbols=BTC,ETH,SOL&exchange=OKX&interval=1h&limit=20"
```

Сканировать все фьючерсы через API:

```bash
curl "http://localhost:8000/screener?all_futures=true&max_symbols=200&exchange=OKX&interval=1h&limit=20"
```

## Настройки (env)

- (не требуется) — для режима бирж ключи не нужны

## Примечания

- **Символы**: в UI/CLI вводите базовую монету `BTC,ETH,SOL`. Клиент сам приведёт к нужному формату (например, Binance/Bybit используют `BTCUSDT`).
- **Биржи**: сейчас поддерживаются `OKX`, `Binance`, `Bybit`. Учтите, что некоторые API могут быть geo-blocked в зависимости от региона.
- **All futures**: UI/CLI/API умеют подтянуть список всех фьючерсных инструментов биржи и прогнать скринер по нему (есть лимит `max_symbols`).
