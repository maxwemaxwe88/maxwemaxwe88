import asyncio
import ccxt.async_support as ccxt
import pandas as pd
import time
from datetime import datetime, timedelta

class CryptoScreener:
    def __init__(self):
        self.data = {}  # {exchange_name: dataframe}
        # Keep track of previous data to calculate change
        self.history = {} # {exchange_name: {symbol: {timestamp, openInterest}}}
        
        self.exchanges = {
            'binance': ccxt.binance({'options': {'defaultType': 'future'}, 'enableRateLimit': True}),
            'bybit': ccxt.bybit({'options': {'defaultType': 'linear'}, 'enableRateLimit': True}),
            'okx': ccxt.okx({'options': {'defaultType': 'swap'}, 'enableRateLimit': True}),
            'bitget': ccxt.bitget({'options': {'defaultType': 'swap'}, 'enableRateLimit': True}),
            'deribit': ccxt.deribit({'enableRateLimit': True}),
        }
        self.running = False

    async def close(self):
        for name, exchange in self.exchanges.items():
            await exchange.close()

    async def fetch_exchange_data(self, exchange_name, exchange):
        print(f"[{exchange_name}] Starting fetch...")
        try:
            await exchange.load_markets()
            
            # Filter symbols: USDT perps mainly
            symbols = []
            for symbol, market in exchange.markets.items():
                if market.get('swap') or market.get('future'):
                    # Prioritize USDT pairs or general PERPS
                    if symbol.endswith(':USDT') or symbol.endswith('/USDT'):
                        symbols.append(symbol)
                    elif exchange_name == 'deribit' and symbol.endswith('PERPETUAL'):
                        symbols.append(symbol)
            
            # Limit symbols for MVP performance
            # symbols = symbols[:50] 
            print(f"[{exchange_name}] Found {len(symbols)} symbols. processing...")

            results = []
            
            # Batched fetching
            batch_size = 10
            # Process in chunks
            for i in range(0, len(symbols), batch_size):
                batch = symbols[i:i+batch_size]
                tasks = [self.fetch_symbol_data(exchange, s) for s in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for res in batch_results:
                    if isinstance(res, dict):
                        results.append(res)
                
                # Rate limit sleep - dynamic based on exchange could be better but fixed is ok
                await asyncio.sleep(0.1)

            df = pd.DataFrame(results)
            if not df.empty:
                df['exchange'] = exchange_name
                
                # Calculate Change since last fetch
                if exchange_name in self.data:
                    old_df = self.data[exchange_name]
                    # Create a mapping of symbol -> OI
                    old_oi_map = dict(zip(old_df['symbol'], old_df['openInterest']))
                    
                    def calc_change(row):
                        old_oi = old_oi_map.get(row['symbol'])
                        if old_oi and old_oi > 0:
                            return ((row['openInterest'] - old_oi) / old_oi) * 100
                        return 0
                    
                    df['openInterestChange1h'] = df.apply(calc_change, axis=1)
                else:
                    df['openInterestChange1h'] = 0.0

                self.data[exchange_name] = df
                print(f"[{exchange_name}] Updated {len(df)} records.")
            else:
                print(f"[{exchange_name}] No data found.")

        except Exception as e:
            print(f"[{exchange_name}] Error fetching data: {e}")

    async def fetch_symbol_data(self, exchange, symbol):
        try:
            # 1. Fetch Ticker (Price, Vol)
            ticker = await exchange.fetch_ticker(symbol)
            price = ticker.get('last')
            vol_24h = ticker.get('quoteVolume') 

            # 2. Fetch Open Interest (Current)
            oi = await exchange.fetch_open_interest(symbol)
            oi_val = oi.get('openInterestValue')
            oi_amt = oi.get('openInterestAmount')
            
            if oi_val is None and oi_amt and price:
                oi_val = oi_amt * price
            
            # 3. Simulate Change (or fetch history if possible)
            # For now return 0 change, frontend will sort by OI value or we add history fetching later
            oi_change = 0 

            return {
                'symbol': symbol,
                'price': price,
                'openInterest': oi_val,
                'openInterestChange1h': oi_change, # Placeholder
                'volume24h': vol_24h,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return None

    async def update_loop(self):
        self.running = True
        while self.running:
            tasks = [self.fetch_exchange_data(name, exc) for name, exc in self.exchanges.items()]
            await asyncio.gather(*tasks)
            print("All exchanges updated. Sleeping 60s...")
            await asyncio.sleep(60)

    def get_all_data(self):
        all_data = []
        for name, df in self.data.items():
            if not df.empty:
                records = df.to_dict('records')
                all_data.extend(records)
        return all_data

screener = CryptoScreener()
