"""Bitget Futures OI data fetcher."""
import httpx
import time
from typing import List
from .base import BaseExchange, OIData


class BitgetExchange(BaseExchange):
    """Bitget exchange integration."""
    
    name = "bitget"
    display_name = "Bitget"
    
    BASE_URL = "https://api.bitget.com"
    
    async def fetch_oi_data(self) -> List[OIData]:
        """Fetch OI data from Bitget."""
        results = []
        current_time = int(time.time())
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get all USDT-M futures tickers
                tickers_resp = await client.get(
                    f"{self.BASE_URL}/api/v2/mix/market/tickers",
                    params={"productType": "USDT-FUTURES"}
                )
                tickers_data = tickers_resp.json()
                
                if tickers_data.get('code') != '00000':
                    print(f"Bitget API error: {tickers_data.get('msg')}")
                    return results
                
                tickers = tickers_data.get('data', [])
                
                for ticker in tickers:
                    symbol = ticker.get('symbol', '')
                    if not symbol:
                        continue
                    
                    try:
                        price = float(ticker.get('lastPr', 0))
                        oi_value = float(ticker.get('openUtc', 0))
                        volume_24h = float(ticker.get('usdtVolume', 0))
                        
                        # Try to get OI from open interest endpoint
                        try:
                            oi_resp = await client.get(
                                f"{self.BASE_URL}/api/v2/mix/market/open-interest",
                                params={
                                    "symbol": symbol,
                                    "productType": "USDT-FUTURES"
                                }
                            )
                            oi_data = oi_resp.json()
                            if oi_data.get('code') == '00000' and oi_data.get('data'):
                                oi_info = oi_data['data']
                                oi_qty = float(oi_info.get('openInterestCont', 0))
                                oi_value = oi_qty * price
                        except:
                            pass
                        
                        if oi_value <= 0:
                            continue
                        
                        change_5m, change_1h, change_24h = self.calculate_oi_change(
                            symbol, oi_value, current_time
                        )
                        
                        # Format symbol: BTCUSDT -> BTC
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
                print(f"Bitget error: {e}")
        
        self.last_update = current_time
        return results
