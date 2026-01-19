import argparse
import sys
from screener import OIScreener

def main():
    parser = argparse.ArgumentParser(description="Coinglass Open Interest Screener")
    parser.add_argument("--symbols", type=str, help="Comma separated list of symbols to screen (e.g. BTC,ETH,SOL)")
    parser.add_argument("--top", type=int, help="Number of top coins to screen (default 10)", default=10)
    
    args = parser.parse_args()

    screener = OIScreener()
    
    if args.symbols:
        coins = [s.strip().upper() for s in args.symbols.split(',')]
    else:
        # Get default supported coins. 
        # In a real app, we might want to fetch the top N coins dynamically.
        # For now, we use the hardcoded list in API class, or extend it.
        coins = screener.api.get_supported_coins()
        if len(coins) > args.top:
            coins = coins[:args.top]

    print(f"Screening Open Interest for: {', '.join(coins)}")
    df = screener.get_oi_data(coins)
    screener.display_screener(df)

if __name__ == "__main__":
    main()
