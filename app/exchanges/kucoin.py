"""KuCoin Futures OI data fetcher."""
import httpx
import time
from typing import List
from .base import BaseExchange, OIData


class KuCoinExchange(BaseExchange):
    """KuCoin exchange integration."""
    
    name = "kucoin"
    display_name = "KuCoin"
    
    BASE_URL = "https://api-futures.kucoin.com"
    
    async def fetch_oi_data(self) -> List[OIData]:
        """Fetch OI data from KuCoin Futures."""
        results = []
        current_time = int(time.time())
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get all contracts
                contracts_resp = await client.get(
                    f"{self.BASE_URL}/api/v1/contracts/active"
                )
                contracts_data = contracts_resp.json()
                
                if contracts_data.get('code') != '200000':
                    return results
                
                contracts = contracts_data.get('data', [])
                
                for contract in contracts:
                    symbol = contract.get('symbol', '')
                    if not symbol.endswith('USDTM'):
                        continue
                    
                    try:
                        # Get ticker for this contract
                        ticker_resp = await client.get(
                            f"{self.BASE_URL}/api/v1/ticker",
                            params={"symbol": symbol}
                        )
                        ticker_data = ticker_resp.json()
                        
                        if ticker_data.get('code') != '200000':
                            continue
                        
                        ticker = ticker_data.get('data', {})
                        
                        price = float(ticker.get('price', 0))
                        oi_qty = float(contract.get('openInterest', 0))
                        multiplier = float(contract.get('multiplier', 1))
                        oi_value = oi_qty * multiplier
                        volume_24h = float(ticker.get('turnover', 0))
                        
                        if oi_value <= 0:
                            continue
                        
                        change_5m, change_1h, change_24h = self.calculate_oi_change(
                            symbol, oi_value, current_time
                        )
                        
                        # Format symbol: XBTUSDTM -> XBT
                        display_symbol = symbol.replace('USDTM', '')
                        if display_symbol == 'XBT':
                            display_symbol = 'BTC'
                        
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
                print(f"KuCoin error: {e}")
        
        self.last_update = current_time
        return results
