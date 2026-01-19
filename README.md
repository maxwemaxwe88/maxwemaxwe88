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

На Windows/локально удобнее один раз создать файл `.env` рядом с `pyproject.toml` (он уже в `.gitignore`):

```env
COINGLASS_API_KEY=YOUR_KEY
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

5) Визуальный клиент (UI в браузере):

```bash
coinglass-oi ui --port 8501
```

Открыть в браузере: `http://localhost:8501`

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

- Эндпоинт Coinglass для истории OI иногда отличается по названию/версии. В CLI/HTTP можно передать `endpoint_path` (по умолчанию `open_interest_history`).
- По факту у Coinglass есть “рабочий” вариант snake_case: `open_interest_history` (в некоторых окружениях `openInterestHistory` возвращает 500).
