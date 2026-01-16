"""LBank Futures OI data fetcher."""
import httpx
import time
from typing import List
from .base import BaseExchange, OIData


class LBankExchange(BaseExchange):
    """LBank exchange integration."""
    
    name = "lbank"
    display_name = "LBank"
    
    BASE_URL = "https://lbkperp.lbank.com"
    
    async def fetch_oi_data(self) -> List[OIData]:
        """Fetch OI data from LBank Futures."""
        results = []
        current_time = int(time.time())
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get all tickers
                tickers_resp = await client.get(
                    f"{self.BASE_URL}/cfd/openApi/v1/pub/marketData"
                )
                tickers_data = tickers_resp.json()
                
                if tickers_data.get('code') != '0':
                    return results
                
                tickers = tickers_data.get('data', [])
                
                for ticker in tickers:
                    symbol = ticker.get('symbol', '')
                    if not symbol.endswith('USDT'):
                        continue
                    
                    try:
                        price = float(ticker.get('lastPrice', 0))
                        oi_value = float(ticker.get('openInterest', 0))
                        volume_24h = float(ticker.get('turnover24h', 0))
                        
                        if oi_value <= 0:
                            continue
                        
                        change_5m, change_1h, change_24h = self.calculate_oi_change(
                            symbol, oi_value, current_time
                        )
                        
                        display_symbol = symbol.replace('USDT', '').replace('_', '')
                        
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
                print(f"LBank error: {e}")
        
        self.last_update = current_time
        return results
