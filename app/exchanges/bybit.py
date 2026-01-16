"""Bybit Futures OI data fetcher."""
import httpx
import time
from typing import List
from .base import BaseExchange, OIData


class BybitExchange(BaseExchange):
    """Bybit exchange integration."""
    
    name = "bybit"
    display_name = "Bybit"
    
    BASE_URL = "https://api.bybit.com"
    
    async def fetch_oi_data(self) -> List[OIData]:
        """Fetch OI data from Bybit."""
        results = []
        current_time = int(time.time())
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get tickers with OI data
                resp = await client.get(
                    f"{self.BASE_URL}/v5/market/tickers",
                    params={"category": "linear"}
                )
                data = resp.json()
                
                if data.get('retCode') != 0:
                    print(f"Bybit API error: {data.get('retMsg')}")
                    return results
                
                tickers = data.get('result', {}).get('list', [])
                
                for ticker in tickers:
                    symbol = ticker.get('symbol', '')
                    if not symbol.endswith('USDT'):
                        continue
                    
                    try:
                        price = float(ticker.get('lastPrice', 0))
                        oi_value = float(ticker.get('openInterestValue', 0))
                        volume_24h = float(ticker.get('turnover24h', 0))
                        
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
                        
                    except Exception as e:
                        continue
                
            except Exception as e:
                print(f"Bybit error: {e}")
        
        self.last_update = current_time
        return results
