"""CoinEx Futures OI data fetcher."""
import httpx
import time
from typing import List
from .base import BaseExchange, OIData


class CoinExExchange(BaseExchange):
    """CoinEx exchange integration."""
    
    name = "coinex"
    display_name = "CoinEx"
    
    BASE_URL = "https://api.coinex.com"
    
    async def fetch_oi_data(self) -> List[OIData]:
        """Fetch OI data from CoinEx Futures."""
        results = []
        current_time = int(time.time())
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get market list
                markets_resp = await client.get(
                    f"{self.BASE_URL}/perpetual/v1/market/list"
                )
                markets_data = markets_resp.json()
                
                if markets_data.get('code') != 0:
                    return results
                
                markets = markets_data.get('data', [])
                
                # Get tickers
                tickers_resp = await client.get(
                    f"{self.BASE_URL}/perpetual/v1/market/ticker/all"
                )
                tickers_data = tickers_resp.json()
                
                ticker_map = tickers_data.get('data', {}).get('ticker', {})
                
                for market in markets:
                    symbol = market.get('name', '')
                    if not symbol.endswith('USDT'):
                        continue
                    
                    ticker = ticker_map.get(symbol, {})
                    
                    try:
                        price = float(ticker.get('last', 0))
                        oi_qty = float(ticker.get('open_interest', 0))
                        oi_value = oi_qty * price
                        volume_24h = float(ticker.get('volume', 0)) * price
                        
                        if oi_value <= 0:
                            continue
                        
                        change_5m, change_1h, change_24h = self.calculate_oi_change(
                            symbol, oi_value, current_time
                        )
                        
                        # Format symbol
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
                print(f"CoinEx error: {e}")
        
        self.last_update = current_time
        return results
