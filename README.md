# Coinglass Open Interest Screener

This is a Python-based Open Interest screener that uses the Coinglass API to fetch and display Open Interest data for cryptocurrency pairs.

## Prerequisites

- Python 3.8+
- A Coinglass API Key (You can get one from [Coinglass API](https://coinglass.github.io/API-Reference/))

## Installation

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and add your Coinglass API Key:
   ```bash
   cp .env.example .env
   # Edit .env and set COINGLASS_API_KEY
   ```

## Usage

Run the screener with default settings (Top 10 coins):

```bash
python main.py
```

Specify coins to screen:

```bash
python main.py --symbols BTC,ETH,SOL,XRP
```

Limit the number of top coins (if using default list):

```bash
python main.py --top 5
```

## Structure

- `coinglass_api.py`: Handles interaction with Coinglass API.
- `screener.py`: Contains the logic to fetch and aggregate data.
- `main.py`: CLI entry point.

## License

MIT
