import asyncio
import ccxt.async_support as ccxt

async def check_exchanges():
    # Exchanges from the image that might have Futures/OI
    new_exchanges = [
        'gate', 'kucoin', 'mexc', 'bingx', 'huobi', 'bitmart', 'hyperliquid', 'lbank'
    ]
    
    print("Checking CCXT capabilities for new exchanges...")
    
    for exchange_id in new_exchanges:
        if not hasattr(ccxt, exchange_id):
            print(f"❌ {exchange_id}: Not found in CCXT")
            continue
            
        try:
            exchange_class = getattr(ccxt, exchange_id)
            exchange = exchange_class()
            
            # Check for fetchOpenInterest capability
            # We assume 'swap' or 'future' markets are what we want
            has_oi = exchange.has.get('fetchOpenInterest')
            print(f"✅ {exchange_id}: Found in CCXT. fetchOpenInterest={has_oi}")
            
            await exchange.close()
        except Exception as e:
            print(f"⚠️ {exchange_id}: Error checking: {e}")

if __name__ == "__main__":
    asyncio.run(check_exchanges())
