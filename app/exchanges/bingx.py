"""BingX Futures OI data fetcher."""
import httpx
import time
from typing import List
from .base import BaseExchange, OIData


class BingXExchange(BaseExchange):
    """BingX exchange integration."""
    
    name = "bingx"
    display_name = "BingX"
    
    BASE_URL = "https://open-api.bingx.com"
    
    async def fetch_oi_data(self) -> List[OIData]:
        """Fetch OI data from BingX."""
        results = []
        current_time = int(time.time())
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get all contracts
                contracts_resp = await client.get(
                    f"{self.BASE_URL}/openApi/swap/v2/quote/contracts"
                )
                contracts_data = contracts_resp.json()
                
                if contracts_data.get('code') != 0:
                    return results
                
                contracts = contracts_data.get('data', [])
                
                # Get tickers
                tickers_resp = await client.get(
                    f"{self.BASE_URL}/openApi/swap/v2/quote/ticker"
                )
                tickers_data = tickers_resp.json()
                
                ticker_map = {}
                for t in tickers_data.get('data', []):
                    ticker_map[t.get('symbol', '')] = t
                
                for contract in contracts:
                    symbol = contract.get('symbol', '')
                    if not symbol.endswith('-USDT'):
                        continue
                    
                    ticker = ticker_map.get(symbol, {})
                    
                    try:
                        price = float(ticker.get('lastPrice', 0))
                        oi_value = float(ticker.get('openInterest', 0))
                        volume_24h = float(ticker.get('quoteVolume', 0))
                        
                        if oi_value <= 0:
                            continue
                        
                        change_5m, change_1h, change_24h = self.calculate_oi_change(
                            symbol, oi_value, current_time
                        )
                        
                        # Format symbol: BTC-USDT -> BTC
                        display_symbol = symbol.replace('-USDT', '')
                        
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
                print(f"BingX error: {e}")
        
        self.last_update = current_time
        return results
