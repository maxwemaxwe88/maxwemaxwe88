"""XT.COM Futures OI data fetcher."""
import httpx
import time
from typing import List
from .base import BaseExchange, OIData


class XTExchange(BaseExchange):
    """XT.COM exchange integration."""
    
    name = "xt"
    display_name = "XT.COM"
    
    BASE_URL = "https://fapi.xt.com"
    
    async def fetch_oi_data(self) -> List[OIData]:
        """Fetch OI data from XT.COM Futures."""
        results = []
        current_time = int(time.time())
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get tickers
                tickers_resp = await client.get(
                    f"{self.BASE_URL}/future/market/v1/public/q/tickers"
                )
                tickers_data = tickers_resp.json()
                
                if tickers_data.get('returnCode') != 0:
                    return results
                
                tickers = tickers_data.get('result', [])
                
                for ticker in tickers:
                    symbol = ticker.get('s', '')  # symbol
                    if not symbol.endswith('_usdt'):
                        continue
                    
                    try:
                        price = float(ticker.get('c', 0))  # close/last price
                        oi_qty = float(ticker.get('oi', 0))  # open interest
                        oi_value = oi_qty * price
                        volume_24h = float(ticker.get('q', 0))  # quote volume
                        
                        if oi_value <= 0:
                            continue
                        
                        change_5m, change_1h, change_24h = self.calculate_oi_change(
                            symbol, oi_value, current_time
                        )
                        
                        # Format: btc_usdt -> BTC
                        display_symbol = symbol.replace('_usdt', '').upper()
                        
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
                print(f"XT error: {e}")
        
        self.last_update = current_time
        return results
