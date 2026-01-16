"""OKX Futures OI data fetcher."""
import httpx
import time
from typing import List
from .base import BaseExchange, OIData


class OKXExchange(BaseExchange):
    """OKX exchange integration."""
    
    name = "okx"
    display_name = "OKX"
    
    BASE_URL = "https://www.okx.com"
    
    async def fetch_oi_data(self) -> List[OIData]:
        """Fetch OI data from OKX."""
        results = []
        current_time = int(time.time())
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get all SWAP instruments
                instruments_resp = await client.get(
                    f"{self.BASE_URL}/api/v5/public/instruments",
                    params={"instType": "SWAP"}
                )
                instruments_data = instruments_resp.json()
                
                if instruments_data.get('code') != '0':
                    return results
                
                instruments = instruments_data.get('data', [])
                
                # Get tickers
                tickers_resp = await client.get(
                    f"{self.BASE_URL}/api/v5/market/tickers",
                    params={"instType": "SWAP"}
                )
                tickers_data = tickers_resp.json()
                
                ticker_map = {}
                for t in tickers_data.get('data', []):
                    ticker_map[t.get('instId', '')] = t
                
                # Get open interest
                oi_resp = await client.get(
                    f"{self.BASE_URL}/api/v5/public/open-interest",
                    params={"instType": "SWAP"}
                )
                oi_data = oi_resp.json()
                
                oi_map = {}
                for o in oi_data.get('data', []):
                    oi_map[o.get('instId', '')] = o
                
                for inst in instruments:
                    inst_id = inst.get('instId', '')
                    if not inst_id.endswith('-USDT-SWAP'):
                        continue
                    
                    ticker = ticker_map.get(inst_id, {})
                    oi_info = oi_map.get(inst_id, {})
                    
                    try:
                        price = float(ticker.get('last', 0))
                        oi_qty = float(oi_info.get('oi', 0))
                        ct_val = float(inst.get('ctVal', 1))
                        oi_value = oi_qty * ct_val * price
                        volume_24h = float(ticker.get('volCcy24h', 0))
                        
                        if oi_value <= 0:
                            continue
                        
                        change_5m, change_1h, change_24h = self.calculate_oi_change(
                            inst_id, oi_value, current_time
                        )
                        
                        # Format symbol: BTC-USDT-SWAP -> BTC
                        display_symbol = inst_id.replace('-USDT-SWAP', '')
                        
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
                print(f"OKX error: {e}")
        
        self.last_update = current_time
        return results
