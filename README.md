# 📊 Coinglass Open Interest Screener

Скринер открытого интереса (Open Interest) для криптовалютных деривативов с использованием данных Coinglass API.

## 🚀 Возможности

- **Мониторинг Open Interest** - отслеживание OI по всем топ-криптовалютам
- **Изменения OI** - анализ изменений за 1h, 4h, 24h
- **Топ Gainers/Losers** - монеты с наибольшим ростом/падением OI
- **Необычная активность** - обнаружение аномальных изменений OI
- **Дивергенция OI/Цена** - сигналы потенциального разворота тренда
- **Фильтрация по биржам** - Binance, OKX, Bybit, Bitget и др.
- **CLI и Web интерфейс** - удобное использование из терминала или браузера

## 📋 Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd coinglass-screener
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка API ключа

Получите API ключ на [Coinglass](https://www.coinglass.com/pricing) и настройте его:

```bash
# Способ 1: Переменная окружения
export COINGLASS_API_KEY=your_api_key_here

# Способ 2: Файл .env
cp .env.example .env
# Отредактируйте .env и добавьте ваш ключ
```

## 🖥️ Использование CLI

### Основные команды

```bash
# Просмотр всех команд
python main.py --help

# Скринер с фильтрами
python main.py screen --limit 20 --min-oi 5000000 --sort oi_24h

# Топ гейнеры OI
python main.py gainers --timeframe 4h --limit 15

# Топ лузеры OI  
python main.py losers --timeframe 24h --limit 15

# Необычная активность
python main.py unusual --threshold 5.0 --limit 20

# Дивергенция OI/Цена
python main.py divergence --limit 15

# Общая статистика рынка
python main.py summary

# Информация по монете
python main.py info BTC

# Режим наблюдения (автообновление)
python main.py watch --interval 60

# Экспорт данных
python main.py export --format csv --output data.csv
```

### Параметры скринера

| Параметр | Описание | Значения |
|----------|----------|----------|
| `--limit`, `-l` | Количество результатов | 1-100 |
| `--exchange`, `-e` | Фильтр по бирже | Binance, OKX, Bybit... |
| `--min-oi` | Минимальный OI в USD | число |
| `--sort`, `-s` | Сортировка | oi, oi_1h, oi_4h, oi_24h, price, volume |
| `--asc/--desc` | Порядок сортировки | по умолчанию desc |

### Примеры

```bash
# Топ 20 монет по OI на Binance
python main.py screen --exchange Binance --limit 20

# Монеты с OI > $10M и ростом OI за 4h
python main.py screen --min-oi 10000000 --sort oi_4h --desc

# Сигналы дивергенции для крупных монет
python main.py divergence --min-oi 5000000

# Экспорт в JSON
python main.py export --format json --output oi_data.json
```

## 🌐 Веб-интерфейс

### Запуск

```bash
python app.py
```

Откройте в браузере: http://localhost:5000

### Функции веб-интерфейса

- **Dashboard** - статистика рынка
- **Screener** - таблица с фильтрами
- **Top Gainers** - рост OI
- **Top Losers** - падение OI
- **Unusual Activity** - аномалии
- **Divergence** - сигналы разворота

### API Endpoints

| Endpoint | Описание |
|----------|----------|
| `GET /api/oi` | Данные OI с фильтрами |
| `GET /api/gainers` | Топ гейнеры |
| `GET /api/losers` | Топ лузеры |
| `GET /api/unusual` | Необычная активность |
| `GET /api/divergence` | Сигналы дивергенции |
| `GET /api/summary` | Статистика рынка |
| `GET /api/health` | Проверка состояния |

## 📊 Интерпретация данных

### Open Interest (OI)

**Open Interest** - сумма всех открытых позиций на рынке деривативов.

- **Рост OI + Рост цены** = Сильный бычий тренд
- **Рост OI + Падение цены** = Сильный медвежий тренд
- **Падение OI + Рост цены** = Слабый рост (закрытие шортов)
- **Падение OI + Падение цены** = Слабое падение (закрытие лонгов)

### Сигналы дивергенции

- **BULLISH** (🟢): Цена падает, но OI растет - потенциальный разворот вверх
- **BEARISH** (🔴): Цена растет, но OI падает - потенциальный разворот вниз

### Необычная активность

Монеты с изменением OI > 5% за короткий период могут указывать на:
- Накопление крупных позиций
- Предстоящую волатильность
- Инсайдерскую активность

## 🔧 Структура проекта

```
coinglass-screener/
├── main.py              # CLI интерфейс
├── app.py               # Web интерфейс (Flask)
├── requirements.txt     # Зависимости
├── .env.example         # Пример конфигурации
├── src/
│   ├── __init__.py
│   ├── config.py        # Конфигурация
│   ├── coinglass_api.py # API клиент
│   └── screener.py      # Логика скринера
└── templates/
    └── index.html       # Web UI
```

## 📡 Поддерживаемые биржи

- Binance
- OKX
- Bybit
- Bitget
- dYdX
- Huobi
- Gate
- CoinEx
- Kraken
- Bitmex

## ⚠️ Важно

1. **API ключ** - для полного доступа требуется платный API ключ Coinglass
2. **Rate limits** - не превышайте лимиты запросов API
3. **Не финансовый совет** - данные предоставляются только для информационных целей

## 📝 Лицензия

MIT License

## 🤝 Вклад

Приветствуются pull requests и issues!
