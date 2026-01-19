# Coinglass Open Interest Screener

Скринер изменения **Open Interest** по списку тикеров, завязанный на **Coinglass Open API**.

## Быстрый старт

1) Установить зависимости:

```bash
python -m pip install -e .
```

2) Задать ключ Coinglass:

```bash
export COINGLASS_API_KEY="YOUR_KEY"
```

Если у вашего аккаунта другой заголовок для ключа, можно переопределить:

```bash
export COINGLASS_API_KEY_HEADER="coinglassSecret"
```

3) Запуск CLI-скринера:

```bash
coinglass-oi screen --symbols BTC,ETH,SOL --interval 1h --limit 20
```

4) Запуск HTTP API:

```bash
coinglass-oi serve --port 8000
```

Пример запроса:

```bash
curl "http://localhost:8000/screener?symbols=BTC,ETH,SOL&interval=1h&limit=20"
```

## Настройки (env)

- `COINGLASS_API_KEY`: API key
- `COINGLASS_API_BASE_URL`: базовый URL (по умолчанию `https://open-api.coinglass.com/public/v2`)
- `COINGLASS_API_KEY_HEADER`: имя заголовка с ключом (по умолчанию `coinglassSecret`)
- `COINGLASS_TIMEOUT_S`: таймаут HTTP запросов

## Примечания

- Эндпоинт Coinglass для истории OI иногда отличается по названию/версии. В CLI/HTTP можно передать `endpoint_path` (по умолчанию `openInterestHistory`).
