"""BitMart Futures OI data fetcher."""
import httpx
import time
from typing import List
from .base import BaseExchange, OIData


class BitMartExchange(BaseExchange):
    """BitMart exchange integration."""
    
    name = "bitmart"
    display_name = "BitMart"
    
    BASE_URL = "https://api-cloud.bitmart.com"
    
    async def fetch_oi_data(self) -> List[OIData]:
        """Fetch OI data from BitMart Futures."""
        results = []
        current_time = int(time.time())
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get contract details
                contracts_resp = await client.get(
                    f"{self.BASE_URL}/contract/public/details"
                )
                contracts_data = contracts_resp.json()
                
                if contracts_data.get('code') != 1000:
                    return results
                
                contracts = contracts_data.get('data', {}).get('symbols', [])
                
                # Get tickers
                tickers_resp = await client.get(
                    f"{self.BASE_URL}/contract/public/tickers"
                )
                tickers_data = tickers_resp.json()
                
                ticker_map = {}
                for t in tickers_data.get('data', {}).get('tickers', []):
                    ticker_map[t.get('symbol', '')] = t
                
                for contract in contracts:
                    symbol = contract.get('symbol', '')
                    if not symbol.endswith('USDT'):
                        continue
                    
                    ticker = ticker_map.get(symbol, {})
                    
                    try:
                        price = float(ticker.get('last_price', 0))
                        oi_value = float(ticker.get('open_interest_value', 0))
                        volume_24h = float(ticker.get('volume_24h', 0))
                        
                        if oi_value <= 0:
                            continue
                        
                        change_5m, change_1h, change_24h = self.calculate_oi_change(
                            symbol, oi_value, current_time
                        )
                        
                        display_symbol = symbol.replace('USDT', '')
                        
                        results.append(OIData(
                            symbol=display_symbol,
                            price=price,
                            oi_value=oi_value,
                            oi_change_5m=change_5m,
                            oi_change_1h=change_1h,
                            oi_change_24h=change_24h,
                            volume_24h=volume_24h,
                            timestamp=current_time
                        ))
                    except Exception:
                        continue
                
            except Exception as e:
                print(f"BitMart error: {e}")
        
        self.last_update = current_time
        return results
