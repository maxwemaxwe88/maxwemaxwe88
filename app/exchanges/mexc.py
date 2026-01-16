"""MEXC Futures OI data fetcher."""
import httpx
import time
from typing import List
from .base import BaseExchange, OIData


class MEXCExchange(BaseExchange):
    """MEXC exchange integration."""
    
    name = "mexc"
    display_name = "MEXC"
    
    BASE_URL = "https://contract.mexc.com"
    
    async def fetch_oi_data(self) -> List[OIData]:
        """Fetch OI data from MEXC."""
        results = []
        current_time = int(time.time())
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get all contract details
                contracts_resp = await client.get(
                    f"{self.BASE_URL}/api/v1/contract/detail"
                )
                contracts_data = contracts_resp.json()
                
                if not contracts_data.get('success'):
                    return results
                
                contracts = contracts_data.get('data', [])
                
                # Get tickers
                tickers_resp = await client.get(
                    f"{self.BASE_URL}/api/v1/contract/ticker"
                )
                tickers_data = tickers_resp.json()
                
                ticker_map = {}
                for t in tickers_data.get('data', []):
                    ticker_map[t.get('symbol', '')] = t
                
                for contract in contracts:
                    symbol = contract.get('symbol', '')
                    if not symbol.endswith('_USDT'):
                        continue
                    
                    ticker = ticker_map.get(symbol, {})
                    
                    try:
                        price = float(ticker.get('lastPrice', 0))
                        oi_qty = float(ticker.get('holdVol', 0))
                        contract_size = float(contract.get('contractSize', 1))
                        oi_value = oi_qty * contract_size * price
                        volume_24h = float(ticker.get('amount24', 0))
                        
                        if oi_value <= 0:
                            continue
                        
                        change_5m, change_1h, change_24h = self.calculate_oi_change(
                            symbol, oi_value, current_time
                        )
                        
                        # Format symbol: BTC_USDT -> BTC
                        display_symbol = symbol.replace('_USDT', '')
                        
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
                print(f"MEXC error: {e}")
        
        self.last_update = current_time
        return results
