import asyncio
import ccxt.async_support as ccxt

async def probe_specifics():
    exchanges = {
        'gate': ccxt.gate(),
        'kucoin': ccxt.kucoin(),
        'mexc': ccxt.mexc()
    }
    
    # Symbols to test (standard perps)
    test_symbols = {
        'gate': 'BTC_USDT', # Gate futures usually denote like this
        'kucoin': 'XBTUSDTM', # Kucoin futures
        'mexc': 'BTC_USDT'
    }

    print("Probing specific APIs for Open Interest...")

    for name, exchange in exchanges.items():
        try:
            print(f"\n--- {name} ---")
            await exchange.load_markets()
            
            # Try to find a valid swap symbol
            symbol = None
            for s in exchange.symbols:
                if 'USDT' in s and (':USDT' in s or '/USDT' in s):
                    symbol = s
                    break
            
            if not symbol:
                print(f"No suitable symbol found for {name}")
                continue

            print(f"Testing symbol: {symbol}")

            # 1. Try unified fetchTicker (sometimes OI is in info)
            ticker = await exchange.fetch_ticker(symbol)
            if 'openInterest' in ticker and ticker['openInterest']:
                print(f"✅ Found OI in fetchTicker: {ticker['openInterest']}")
            
            # 2. Try fetchOpenInterest directly even if 'has' says false (sometimes it works or we force it)
            try:
                oi = await exchange.fetch_open_interest(symbol)
                print(f"✅ Found OI in fetchOpenInterest: {oi}")
            except Exception as e:
                print(f"❌ fetchOpenInterest failed: {e}")

        except Exception as e:
            print(f"Error checking {name}: {e}")
        finally:
            await exchange.close()

if __name__ == "__main__":
    asyncio.run(probe_specifics())
