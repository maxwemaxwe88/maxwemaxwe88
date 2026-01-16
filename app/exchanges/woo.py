"""WOO X Futures OI data fetcher."""
import httpx
import time
from typing import List
from .base import BaseExchange, OIData


class WOOExchange(BaseExchange):
    """WOO X exchange integration."""
    
    name = "woo"
    display_name = "WOO X"
    
    BASE_URL = "https://api.woo.org"
    
    async def fetch_oi_data(self) -> List[OIData]:
        """Fetch OI data from WOO X Futures."""
        results = []
        current_time = int(time.time())
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get futures info
                info_resp = await client.get(
                    f"{self.BASE_URL}/v1/public/futures"
                )
                info_data = info_resp.json()
                
                if not info_data.get('success'):
                    return results
                
                futures = info_data.get('rows', [])
                
                for fut in futures:
                    symbol = fut.get('symbol', '')
                    if not 'USDT' in symbol:
                        continue
                    
                    try:
                        # Get ticker for this symbol
                        ticker_resp = await client.get(
                            f"{self.BASE_URL}/v1/public/futures/{symbol}"
                        )
                        ticker_data = ticker_resp.json()
                        
                        if not ticker_data.get('success'):
                            continue
                        
                        ticker = ticker_data.get('info', {})
                        
                        price = float(ticker.get('index_price', 0))
                        oi_value = float(ticker.get('open_interest', 0))
                        volume_24h = float(ticker.get('volume', 0))
                        
                        if oi_value <= 0:
                            continue
                        
                        change_5m, change_1h, change_24h = self.calculate_oi_change(
                            symbol, oi_value, current_time
                        )
                        
                        # Format: PERP_BTC_USDT -> BTC
                        display_symbol = symbol.replace('PERP_', '').replace('_USDT', '')
                        
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
                print(f"WOO error: {e}")
        
        self.last_update = current_time
        return results
