import asyncio
import ccxt.async_support as ccxt

async def probe_futures():
    # Configure for Futures/Swap
    exchanges = {
        'gate': ccxt.gate({'options': {'defaultType': 'swap'}}),
        'kucoin': ccxt.kucoin({'options': {'defaultType': 'future'}}),
        'mexc': ccxt.mexc({'options': {'defaultType': 'swap'}})
    }
    
    print("Probing Futures Markets...")

    for name, exchange in exchanges.items():
        try:
            print(f"\n--- {name} ---")
            await exchange.load_markets()
            
            # Find a valid Swap symbol
            target_symbol = None
            market_id = None
            for s, m in exchange.markets.items():
                if m['swap']:
                    target_symbol = s
                    market_id = m['id']
                    break
            
            if not target_symbol:
                print("No swap markets found")
                continue
                
            print(f"Target: {target_symbol} (ID: {market_id})")

            # Check Ticker
            ticker = await exchange.fetch_ticker(target_symbol)
            # print("Ticker keys:", ticker.keys())
            if 'openInterest' in ticker:
                print(f"✅ OI in ticker: {ticker['openInterest']}")
            elif 'info' in ticker:
                 # Check raw info
                 print(f"Checking raw ticker info keys: {list(ticker['info'].keys())}")
                 # Gate usually has 'open_interest_usd' or similar
                 
            # Try specific methods if known
            if name == 'gate':
                # Gate has different tiers (usdt, etc). 
                # Try publicFuturesUsdtGetTickers
                try:
                    if hasattr(exchange, 'publicFuturesUsdtGetTickers'):
                        tickers = await exchange.publicFuturesUsdtGetTickers({'contract': market_id})
                        if tickers and len(tickers) > 0:
                            print(f"Gate Raw: {tickers[0].get('open_interest_usd')}")
                except Exception as e:
                     print(f"Gate specific failed: {e}")

        except Exception as e:
            print(f"Error {name}: {e}")
        finally:
            await exchange.close()

if __name__ == "__main__":
    asyncio.run(probe_futures())
