# Техническое Задание (ТЗ)
## OI Screener - Скринер открытого интереса криптовалютных фьючерсов

---

## 1. Общее описание проекта

### 1.1 Назначение
Десктопное приложение для мониторинга и анализа изменений открытого интереса (Open Interest, OI) на фьючерсных рынках криптовалют. Приложение агрегирует данные с множества бирж в реальном времени для выявления активности крупных участников рынка.

### 1.2 Целевая аудитория
- Криптовалютные трейдеры
- Алготрейдеры
- Аналитики рынка
- Инвесторы

### 1.3 Аналоги
- Coinglass (coinglass.com)
- TaoScalp (taoscalp.com)
- Kingfisher

---

## 2. Функциональные требования

### 2.1 Поддерживаемые биржи

#### 2.1.1 Централизованные биржи (CEX) - Futures
| Биржа | API | Приоритет |
|-------|-----|-----------|
| Binance USDT-M | fapi.binance.com | Высокий |
| Binance COIN-M | dapi.binance.com | Средний |
| Bybit USDT Perpetual | api.bybit.com | Высокий |
| Bybit USDC Perpetual | api.bybit.com | Средний |
| OKX Futures | okx.com | Высокий |
| Bitget Futures | api.bitget.com | Высокий |
| Gate.io Futures | api.gateio.ws | Высокий |
| MEXC Futures | contract.mexc.com | Средний |
| KuCoin Futures | api-futures.kucoin.com | Средний |
| HTX (Huobi) Futures | api.hbdm.com | Средний |
| Deribit | deribit.com | Средний |
| Phemex | api.phemex.com | Низкий |
| BingX | open-api.bingx.com | Средний |
| CoinEx | api.coinex.com | Низкий |
| BitMart | api-cloud.bitmart.com | Низкий |
| LBank | lbkperp.lbank.com | Низкий |
| WOO X | api.woo.org | Низкий |
| XT.COM | fapi.xt.com | Низкий |

#### 2.1.2 Децентрализованные биржи (DEX)
| Биржа | API | Приоритет |
|-------|-----|-----------|
| HyperLiquid | api.hyperliquid.xyz | Высокий |
| dYdX | indexer.dydx.trade | Средний |
| GMX | api.gmx.io | Низкий |

### 2.2 Отображаемые данные

Для каждого торгового инструмента:
- **Символ** - название монеты (BTC, ETH, etc.)
- **Цена** - текущая цена в USD
- **OI (USD)** - открытый интерес в долларах
- **OI 5м%** - изменение OI за 5 минут
- **OI 1ч%** - изменение OI за 1 час  
- **OI 4ч%** - изменение OI за 4 часа
- **OI 24ч%** - изменение OI за 24 часа
- **Объём 24ч** - торговый объём за 24 часа
- **Funding Rate** - ставка финансирования (опционально)
- **Long/Short Ratio** - соотношение лонгов к шортам (опционально)

### 2.3 Режимы отображения

#### 2.3.1 Мульти-панельный режим (Grid View)
- Каждая биржа в отдельном окне/панели
- 2-4 колонки панелей (настраиваемо)
- Компактный вид таблицы
- Лимит 50 строк на панель

#### 2.3.2 Режим одной биржи (Single View)
- Полноэкранная таблица для выбранной биржи
- Все доступные столбцы
- До 500 строк
- Расширенные фильтры

#### 2.3.3 Агрегированный режим (Aggregate View)
- Объединение данных со всех бирж
- Группировка по символу
- Суммарный OI по всем биржам
- Сравнение OI между биржами

### 2.4 Сортировка и фильтрация

#### 2.4.1 Сортировка
- По любому столбцу
- По возрастанию / убыванию
- Мульти-сортировка (до 3 параметров)

#### 2.4.2 Фильтры
- Минимальный OI (USD)
- Минимальный объём 24ч
- Поиск по символу
- Фильтр по изменению OI (например, >5%)
- Исключение стейблкоинов
- Избранные монеты

### 2.5 Оповещения (Alerts)

#### 2.5.1 Типы алертов
- OI изменился на X% за Y минут
- OI превысил порог в USD
- Аномальный рост OI (статистический)
- Расхождение OI между биржами

#### 2.5.2 Каналы уведомлений
- Звуковое уведомление
- Системное уведомление (notification)
- Telegram бот (опционально)
- Discord webhook (опционально)

### 2.6 Исторические данные

- Хранение OI данных за последние 7 дней
- Графики изменения OI
- Экспорт в CSV/Excel
- Сравнение с историческими пиками

---

## 3. Нефункциональные требования

### 3.1 Производительность
- Обновление данных каждые 5-10 секунд
- Время загрузки приложения < 3 секунд
- Потребление RAM < 500 MB
- Минимальная нагрузка на CPU

### 3.2 Надёжность
- Автоматическое переподключение при потере связи
- Кэширование данных при сбоях API
- Retry логика с exponential backoff
- Graceful degradation при недоступности бирж

### 3.3 Безопасность
- Не требует API ключей (публичные endpoints)
- Локальное хранение настроек
- Без передачи пользовательских данных

---

## 4. Технический стек

### 4.1 Backend
```
Python 3.10+
├── FastAPI - REST API и WebSocket сервер
├── httpx / aiohttp - асинхронные HTTP клиенты
├── asyncio - асинхронная обработка
├── SQLite - локальная база данных
├── Pydantic - валидация данных
└── uvicorn - ASGI сервер
```

### 4.2 Frontend (Desktop)
```
Вариант A: Electron + React/Vue
├── Electron - десктопная оболочка
├── React/Vue - UI фреймворк
├── TailwindCSS - стилизация
├── Recharts/Chart.js - графики
└── WebSocket - real-time обновления

Вариант B: Tauri + React/Svelte
├── Tauri - легковесная десктопная оболочка (Rust)
├── Svelte/React - UI фреймворк
└── Меньшее потребление ресурсов

Вариант C: PyQt/PySide6
├── Python нативный GUI
├── QML для UI
└── Единый стек (Python)
```

### 4.3 Рекомендуемый стек
```
Backend:  Python + FastAPI + SQLite
Frontend: Tauri + Svelte + TailwindCSS
```

---

## 5. Архитектура приложения

### 5.1 Структура проекта

```
oi-screener/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI приложение
│   │   ├── config.py            # Конфигурация
│   │   ├── database.py          # SQLite подключение
│   │   ├── models.py            # Pydantic модели
│   │   ├── exchanges/           # Модули бирж
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Базовый класс
│   │   │   ├── binance.py
│   │   │   ├── bybit.py
│   │   │   └── ...
│   │   ├── services/
│   │   │   ├── aggregator.py    # Агрегация данных
│   │   │   ├── alerts.py        # Система алертов
│   │   │   └── history.py       # Исторические данные
│   │   └── api/
│   │       ├── routes.py        # REST endpoints
│   │       └── websocket.py     # WebSocket handlers
│   ├── requirements.txt
│   └── run.py
│
├── frontend/
│   ├── src/
│   │   ├── App.svelte
│   │   ├── components/
│   │   │   ├── ExchangePanel.svelte
│   │   │   ├── DataTable.svelte
│   │   │   ├── Filters.svelte
│   │   │   ├── Alerts.svelte
│   │   │   └── Settings.svelte
│   │   ├── stores/
│   │   │   ├── exchanges.js
│   │   │   └── settings.js
│   │   └── utils/
│   │       └── formatters.js
│   ├── src-tauri/
│   │   ├── src/
│   │   │   └── main.rs
│   │   ├── Cargo.toml
│   │   └── tauri.conf.json
│   ├── package.json
│   └── vite.config.js
│
├── docs/
│   ├── API.md
│   ├── EXCHANGES.md
│   └── DEPLOYMENT.md
│
└── README.md
```

### 5.2 Диаграмма компонентов

```
┌─────────────────────────────────────────────────────────┐
│                    Desktop App (Tauri)                   │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │              Frontend (Svelte)                   │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐           │   │
│  │  │ Panels  │ │ Tables  │ │ Charts  │           │   │
│  │  └────┬────┘ └────┬────┘ └────┬────┘           │   │
│  │       │           │           │                 │   │
│  │  ┌────┴───────────┴───────────┴────┐           │   │
│  │  │         State Management         │           │   │
│  │  └────────────────┬─────────────────┘           │   │
│  └───────────────────┼──────────────────────────────┘   │
│                      │ WebSocket                         │
├──────────────────────┼──────────────────────────────────┤
│  ┌───────────────────┴──────────────────────────────┐   │
│  │              Backend (FastAPI)                    │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐            │   │
│  │  │   API   │ │ Aggreg  │ │ Alerts  │            │   │
│  │  └────┬────┘ └────┬────┘ └────┬────┘            │   │
│  │       │           │           │                  │   │
│  │  ┌────┴───────────┴───────────┴────┐            │   │
│  │  │        Exchange Manager          │            │   │
│  │  └────────────────┬─────────────────┘            │   │
│  └───────────────────┼──────────────────────────────┘   │
│                      │                                   │
└──────────────────────┼───────────────────────────────────┘
                       │
     ┌─────────────────┼─────────────────┐
     ▼                 ▼                 ▼
┌─────────┐      ┌─────────┐      ┌─────────┐
│ Binance │      │  Bybit  │      │   ...   │
│   API   │      │   API   │      │   APIs  │
└─────────┘      └─────────┘      └─────────┘
```

### 5.3 Поток данных

```
1. Exchange APIs ──► HTTP Client ──► Raw Data
2. Raw Data ──► Parser ──► Normalized OIData
3. OIData ──► Aggregator ──► Cached Data + History
4. Cached Data ──► WebSocket ──► Frontend
5. Frontend ──► Render ──► UI Update
```

---

## 6. API Спецификация

### 6.1 REST Endpoints

```
GET  /api/exchanges
     Список доступных бирж
     Response: { exchanges: [{name, display_name, status}] }

GET  /api/oi
     Данные OI со всех бирж
     Response: { data: {exchange: [OIData]}, timestamp }

GET  /api/oi/{exchange}
     Данные OI с конкретной биржи
     Params: ?sort=oi_change_5m&order=desc&min_oi=100000
     Response: { exchange, data: [OIData], timestamp }

GET  /api/aggregate
     Агрегированные данные по символам
     Response: { data: [{symbol, total_oi, exchanges: [...]}] }

GET  /api/history/{symbol}
     История OI для символа
     Params: ?period=24h
     Response: { symbol, history: [{timestamp, oi_value}] }

POST /api/alerts
     Создать алерт
     Body: { symbol, condition, threshold, channel }

GET  /api/settings
PUT  /api/settings
     Управление настройками
```

### 6.2 WebSocket

```
WS /ws

Client -> Server:
  { type: "subscribe", exchanges: ["binance", "bybit"] }
  { type: "unsubscribe", exchanges: ["mexc"] }
  { type: "ping" }

Server -> Client:
  { type: "initial", data: {...}, exchanges: [...] }
  { type: "update", data: {...}, timestamp }
  { type: "alert", alert: {...} }
  { type: "pong" }
```

### 6.3 Модель данных OIData

```python
class OIData:
    symbol: str           # "BTC"
    price: float          # 95000.50
    oi_value: float       # 5000000000 (USD)
    oi_change_5m: float   # 1.25 (%)
    oi_change_1h: float   # -0.50 (%)
    oi_change_4h: float   # 2.30 (%)
    oi_change_24h: float  # -3.20 (%)
    volume_24h: float     # 10000000000 (USD)
    funding_rate: float   # 0.01 (%)
    timestamp: int        # Unix timestamp
```

---

## 7. Интерфейс пользователя

### 7.1 Главное окно

```
┌─────────────────────────────────────────────────────────────┐
│ ◉ OI Screener                               ● Connected     │
├─────────────────────────────────────────────────────────────┤
│ [Все биржи] [Binance] [Bybit] [OKX] [Bitget] [+]           │
├─────────────────────────────────────────────────────────────┤
│ Sort: [OI 5м% ▼]  Order: [↓ Desc]  Min OI: [100K]  🔍 [...] │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────┐ ┌─────────────────────────┐    │
│ │ Binance          [128] │ │ Bybit            [156] │    │
│ │─────────────────────────│ │─────────────────────────│    │
│ │ SYM   Price    OI  5m%  │ │ SYM   Price    OI  5m%  │    │
│ │ BTC   95000   5.2B +2.5 │ │ BTC   95001   3.1B +2.4 │    │
│ │ ETH   3300    2.1B +1.8 │ │ ETH   3299    1.8B +1.9 │    │
│ │ SOL   145     890M +5.2 │ │ SOL   145     720M +4.8 │    │
│ │ ...                     │ │ ...                     │    │
│ └─────────────────────────┘ └─────────────────────────┘    │
│ ┌─────────────────────────┐ ┌─────────────────────────┐    │
│ │ OKX              [134] │ │ Bitget           [98]  │    │
│ │─────────────────────────│ │─────────────────────────│    │
│ │ ...                     │ │ ...                     │    │
│ └─────────────────────────┘ └─────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│ Last update: 12:34:56 │ Alerts: 3 │ ⚙️ Settings            │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Цветовая схема

```css
/* Тёмная тема (по умолчанию) */
--bg-primary: #0d1117;
--bg-secondary: #161b22;
--bg-tertiary: #21262d;
--border: #30363d;
--text-primary: #c9d1d9;
--text-secondary: #8b949e;
--green: #3fb950;
--red: #f85149;
--accent: #7c3aed;

/* Светлая тема */
--bg-primary: #ffffff;
--bg-secondary: #f6f8fa;
--text-primary: #24292f;
```

### 7.3 Горячие клавиши

| Клавиша | Действие |
|---------|----------|
| `R` | Обновить данные |
| `1-9` | Переключение на биржу |
| `A` | Показать все биржи |
| `F` | Фокус на поиск |
| `Esc` | Закрыть модальное окно |
| `Ctrl+,` | Настройки |
| `Ctrl+E` | Экспорт данных |

---

## 8. План разработки

### Фаза 1: MVP (2 недели)
- [ ] Базовая структура проекта
- [ ] Интеграция 5 основных бирж (Binance, Bybit, OKX, Bitget, Gate)
- [ ] REST API для данных
- [ ] Простой веб-интерфейс
- [ ] Базовая сортировка и фильтрация

### Фаза 2: Core Features (2 недели)
- [ ] WebSocket real-time обновления
- [ ] Добавление остальных бирж
- [ ] Мульти-панельный интерфейс
- [ ] История OI (SQLite)
- [ ] Базовые алерты

### Фаза 3: Desktop App (2 недели)
- [ ] Tauri/Electron оболочка
- [ ] Системные уведомления
- [ ] Настройки и персонализация
- [ ] Горячие клавиши
- [ ] Автозапуск

### Фаза 4: Advanced (2 недели)
- [ ] Графики OI
- [ ] Агрегированный вид
- [ ] Telegram/Discord интеграция
- [ ] Экспорт данных
- [ ] Продвинутые алерты

### Фаза 5: Polish (1 неделя)
- [ ] Тестирование
- [ ] Оптимизация производительности
- [ ] Документация
- [ ] Сборка релиза

---

## 9. Метрики успеха

- Время обновления данных < 10 секунд
- Поддержка 15+ бирж
- 500+ торговых пар
- Стабильная работа 24/7
- Потребление RAM < 500 MB

---

## 10. Ссылки на API документацию бирж

| Биржа | Документация |
|-------|--------------|
| Binance | https://binance-docs.github.io/apidocs/futures/en/ |
| Bybit | https://bybit-exchange.github.io/docs/v5/intro |
| OKX | https://www.okx.com/docs-v5/en/ |
| Bitget | https://bitgetlimited.github.io/apidoc/en/mix/ |
| Gate.io | https://www.gate.io/docs/developers/futures/ |
| MEXC | https://mexcdevelop.github.io/apidocs/contract_v1_en/ |
| KuCoin | https://docs.kucoin.com/futures/ |
| HTX | https://huobiapi.github.io/docs/dm/v1/en/ |
| HyperLiquid | https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api |

---

*Документ создан: Январь 2026*
*Версия: 1.0*
