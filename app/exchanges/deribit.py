"""Deribit Futures OI data fetcher."""
import httpx
import time
from typing import List
from .base import BaseExchange, OIData


class DeribitExchange(BaseExchange):
    """Deribit exchange integration."""
    
    name = "deribit"
    display_name = "Deribit"
    
    BASE_URL = "https://www.deribit.com/api/v2"
    
    async def fetch_oi_data(self) -> List[OIData]:
        """Fetch OI data from Deribit."""
        results = []
        current_time = int(time.time())
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get all instruments
                for currency in ['BTC', 'ETH']:
                    instruments_resp = await client.get(
                        f"{self.BASE_URL}/public/get_instruments",
                        params={"currency": currency, "kind": "future"}
                    )
                    instruments_data = instruments_resp.json()
                    
                    if 'result' not in instruments_data:
                        continue
                    
                    for inst in instruments_data['result']:
                        instrument_name = inst.get('instrument_name', '')
                        
                        # Get ticker for this instrument
                        try:
                            ticker_resp = await client.get(
                                f"{self.BASE_URL}/public/ticker",
                                params={"instrument_name": instrument_name}
                            )
                            ticker_data = ticker_resp.json()
                            
                            if 'result' not in ticker_data:
                                continue
                            
                            ticker = ticker_data['result']
                            
                            price = float(ticker.get('last_price', 0))
                            oi_value = float(ticker.get('open_interest', 0))
                            volume_24h = float(ticker.get('volume_24h', 0)) * price
                            
                            if oi_value <= 0:
                                continue
                            
                            change_5m, change_1h, change_24h = self.calculate_oi_change(
                                instrument_name, oi_value, current_time
                            )
                            
                            results.append(OIData(
                                symbol=instrument_name,
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
                print(f"Deribit error: {e}")
        
        self.last_update = current_time
        return results
