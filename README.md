# Crypto OI Screener

A real-time Open Interest screener for crypto futures, similar to Coinglass.

## Features

- **Multi-Exchange Support**: Fetches data from Binance, Bybit, OKX, Bitget, Deribit.
- **Real-time Data**: Updates Open Interest, Price, and calculated Change.
- **Screener UI**: Grid view of exchanges with sortable tables.
- **Sorting**: Sort by Symbol, Price, Open Interest.

## Project Structure

- `backend/`: Python FastAPI backend using CCXT.
- `frontend/`: React + Vite frontend.

## Setup & Running

### Prerequisites

- Python 3.8+
- Node.js 16+

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The UI will be available at `http://localhost:3000` (or similar).

## Notes

- **Region Restrictions**: Some exchanges (Binance, Bybit) may block connections from certain regions (e.g., US, Cloud IPs). Use a VPN or run locally in a supported region if you see connection errors.
- **Rate Limits**: The fetching logic includes delays to respect API rate limits.
- **Open Interest Change**: Currently simulated or calculated based on runtime cache. For accurate 1h/4h/24h changes, the backend needs to run continuously to build history.

## Development

- Backend logic is in `backend/fetcher.py`.
- Frontend components are in `frontend/src/components/`.
