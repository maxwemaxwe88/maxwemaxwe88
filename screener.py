import pandas as pd
from coinglass_api import CoinglassAPI
from tabulate import tabulate
import time

class OIScreener:
    def __init__(self, api_key=None):
        self.api = CoinglassAPI(api_key)

    def get_oi_data(self, symbols):
        results = []
        print(f"Fetching data for {len(symbols)} symbols...")
        
        for symbol in symbols:
            # Add a small delay to avoid rate limits if necessary
            # time.sleep(0.2) 
            data = self.api.get_open_interest(symbol)
            
            if data:
                # data is usually a list of exchanges
                # We want to aggregate or find the 'All' entry if it exists
                # Usually Coinglass provides detailed breakdown. 
                # Let's sum up the Open Interest
                
                total_oi_usd = 0
                total_oi_amount = 0
                # We can also try to average the changes if provided
                # But it's tricky. Let's just calculate Total OI for now.
                
                # Sometimes the API returns a dict with 'sumOpenInterest' or similar
                # If it's a list, we iterate.
                
                if isinstance(data, list):
                    max_oi = -1
                    proxy_change_1h = None
                    proxy_change_4h = None
                    proxy_change_24h = None

                    for exchange_data in data:
                        # Defensive check for keys
                        oi = exchange_data.get('openInterest', 0)
                        total_oi_usd += oi
                        
                        # Use the exchange with largest OI as proxy for change stats
                        if oi > max_oi:
                            max_oi = oi
                            proxy_change_1h = exchange_data.get('h1OIChangePercent')
                            proxy_change_4h = exchange_data.get('h4OIChangePercent')
                            proxy_change_24h = exchange_data.get('h24OIChangePercent')
                
                results.append({
                    "Symbol": symbol,
                    "Total OI (USD)": total_oi_usd,
                    "1h Change %": proxy_change_1h if proxy_change_1h is not None else "N/A",
                    "4h Change %": proxy_change_4h if proxy_change_4h is not None else "N/A",
                    "24h Change %": proxy_change_24h if proxy_change_24h is not None else "N/A"
                })
            else:
                print(f"No data for {symbol}")

        return pd.DataFrame(results)

    def display_screener(self, df):
        if df.empty:
            print("No data to display.")
            return

        # Sort by OI
        df = df.sort_values(by="Total OI (USD)", ascending=False)
        
        # Format large numbers
        df['Total OI (USD)'] = df['Total OI (USD)'].apply(lambda x: f"${x:,.2f}")
        
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))

if __name__ == "__main__":
    screener = OIScreener()
    coins = screener.api.get_supported_coins()
    df = screener.get_oi_data(coins)
    screener.display_screener(df)
