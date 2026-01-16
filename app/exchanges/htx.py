"""HTX (Huobi) Futures OI data fetcher."""
import httpx
import time
from typing import List
from .base import BaseExchange, OIData


class HTXExchange(BaseExchange):
    """HTX (Huobi) exchange integration."""
    
    name = "htx"
    display_name = "HTX"
    
    BASE_URL = "https://api.hbdm.com"
    
    async def fetch_oi_data(self) -> List[OIData]:
        """Fetch OI data from HTX Linear Swap."""
        results = []
        current_time = int(time.time())
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get all USDT-margined swap contracts info
                contracts_resp = await client.get(
                    f"{self.BASE_URL}/linear-swap-api/v1/swap_contract_info"
                )
                contracts_data = contracts_resp.json()
                
                if contracts_data.get('status') != 'ok':
                    return results
                
                contracts = contracts_data.get('data', [])
                
                # Get market data
                market_resp = await client.get(
                    f"{self.BASE_URL}/linear-swap-ex/market/detail/batch_merged"
                )
                market_data = market_resp.json()
                
                market_map = {}
                for m in market_data.get('ticks', []):
                    market_map[m.get('contract_code', '')] = m
                
                # Get open interest
                oi_resp = await client.get(
                    f"{self.BASE_URL}/linear-swap-api/v1/swap_open_interest"
                )
                oi_data = oi_resp.json()
                
                oi_map = {}
                for o in oi_data.get('data', []):
                    oi_map[o.get('contract_code', '')] = o
                
                for contract in contracts:
                    contract_code = contract.get('contract_code', '')
                    if not contract_code.endswith('-USDT'):
                        continue
                    
                    market = market_map.get(contract_code, {})
                    oi_info = oi_map.get(contract_code, {})
                    
                    try:
                        price = float(market.get('close', 0))
                        oi_value = float(oi_info.get('volume', 0))
                        volume_24h = float(market.get('amount', 0))
                        
                        if oi_value <= 0 or price <= 0:
                            continue
                        
                        # Convert to USD value
                        oi_value = oi_value * price
                        
                        change_5m, change_1h, change_24h = self.calculate_oi_change(
                            contract_code, oi_value, current_time
                        )
                        
                        # Format symbol: BTC-USDT -> BTC
                        display_symbol = contract_code.replace('-USDT', '')
                        
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
                print(f"HTX error: {e}")
        
        self.last_update = current_time
        return results
