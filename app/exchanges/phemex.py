"""Phemex Futures OI data fetcher."""
import httpx
import time
from typing import List
from .base import BaseExchange, OIData


class PhemexExchange(BaseExchange):
    """Phemex exchange integration."""
    
    name = "phemex"
    display_name = "Phemex"
    
    BASE_URL = "https://api.phemex.com"
    
    async def fetch_oi_data(self) -> List[OIData]:
        """Fetch OI data from Phemex."""
        results = []
        current_time = int(time.time())
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get all products
                products_resp = await client.get(f"{self.BASE_URL}/public/products")
                products_data = products_resp.json()
                
                if products_data.get('code') != 0:
                    return results
                
                products = products_data.get('data', {}).get('products', [])
                
                # Get tickers
                tickers_resp = await client.get(f"{self.BASE_URL}/md/v2/ticker/24hr/all")
                tickers_data = tickers_resp.json()
                
                if tickers_data.get('code') != 0:
                    return results
                
                ticker_list = tickers_data.get('data', [])
                ticker_map = {}
                for t in ticker_list:
                    ticker_map[t.get('symbol', '')] = t
                
                for product in products:
                    symbol = product.get('symbol', '')
                    if not symbol.endswith('USDT') or product.get('type') != 'Perpetual':
                        continue
                    
                    ticker = ticker_map.get(symbol, {})
                    
                    try:
                        # Phemex prices are scaled
                        price_scale = float(product.get('priceScale', 8))
                        price = float(ticker.get('lastPr', 0)) / (10 ** price_scale)
                        oi_value = float(ticker.get('openInterest', 0))
                        volume_24h = float(ticker.get('turnoverUsd', 0))
                        
                        if oi_value <= 0:
                            continue
                        
                        change_5m, change_1h, change_24h = self.calculate_oi_change(
                            symbol, oi_value, current_time
                        )
                        
                        # Format symbol
                        display_symbol = symbol.replace('USDT', '').replace('u', '')
                        
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
                print(f"Phemex error: {e}")
        
        self.last_update = current_time
        return results
