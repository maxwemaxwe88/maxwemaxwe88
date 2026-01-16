"""Gate.io Futures OI data fetcher."""
import httpx
import time
from typing import List
from .base import BaseExchange, OIData


class GateExchange(BaseExchange):
    """Gate.io exchange integration."""
    
    name = "gate"
    display_name = "Gate.io"
    
    BASE_URL = "https://api.gateio.ws"
    
    async def fetch_oi_data(self) -> List[OIData]:
        """Fetch OI data from Gate.io."""
        results = []
        current_time = int(time.time())
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get all USDT contracts
                contracts_resp = await client.get(
                    f"{self.BASE_URL}/api/v4/futures/usdt/contracts"
                )
                contracts = contracts_resp.json()
                
                # Get tickers
                tickers_resp = await client.get(
                    f"{self.BASE_URL}/api/v4/futures/usdt/tickers"
                )
                tickers = tickers_resp.json()
                
                ticker_map = {}
                for t in tickers:
                    ticker_map[t.get('contract', '')] = t
                
                for contract in contracts:
                    name = contract.get('name', '')
                    if not name.endswith('_USDT'):
                        continue
                    
                    ticker = ticker_map.get(name, {})
                    
                    try:
                        price = float(ticker.get('last', 0))
                        oi_qty = float(ticker.get('total_size', 0))
                        quanto_multiplier = float(contract.get('quanto_multiplier', 1))
                        oi_value = oi_qty * quanto_multiplier * price
                        volume_24h = float(ticker.get('volume_24h_quote', 0))
                        
                        if oi_value <= 0:
                            continue
                        
                        change_5m, change_1h, change_24h = self.calculate_oi_change(
                            name, oi_value, current_time
                        )
                        
                        # Format symbol: BTC_USDT -> BTC
                        display_symbol = name.replace('_USDT', '')
                        
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
                print(f"Gate.io error: {e}")
        
        self.last_update = current_time
        return results
