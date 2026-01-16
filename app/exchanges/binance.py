"""Binance Futures OI data fetcher."""
import httpx
import time
import asyncio
from typing import List
from .base import BaseExchange, OIData


class BinanceExchange(BaseExchange):
    """Binance Futures exchange integration."""
    
    name = "binance"
    display_name = "Binance"
    
    BASE_URL = "https://fapi.binance.com"
    
    async def fetch_oi_data(self) -> List[OIData]:
        """Fetch OI data from Binance Futures."""
        results = []
        current_time = int(time.time())
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get all futures tickers with price and volume
                ticker_resp = await client.get(f"{self.BASE_URL}/fapi/v1/ticker/24hr")
                tickers = ticker_resp.json()
                
                # Create ticker map
                ticker_map = {}
                usdt_symbols = []
                for t in tickers:
                    if isinstance(t, dict):
                        symbol = t.get('symbol', '')
                        ticker_map[symbol] = t
                        if symbol.endswith('USDT'):
                            usdt_symbols.append(symbol)
                
                # Fetch OI in batches to avoid rate limits
                async def fetch_oi(symbol):
                    try:
                        resp = await client.get(
                            f"{self.BASE_URL}/fapi/v1/openInterest",
                            params={"symbol": symbol}
                        )
                        data = resp.json()
                        return symbol, data.get('openInterest', 0)
                    except:
                        return symbol, 0
                
                # Batch fetch with concurrency limit
                semaphore = asyncio.Semaphore(10)
                
                async def limited_fetch(symbol):
                    async with semaphore:
                        return await fetch_oi(symbol)
                
                oi_results = await asyncio.gather(
                    *[limited_fetch(s) for s in usdt_symbols[:100]]  # Limit to top 100
                )
                
                oi_map = {symbol: oi for symbol, oi in oi_results}
                
                for symbol in usdt_symbols[:100]:
                    ticker = ticker_map.get(symbol, {})
                    oi_qty = float(oi_map.get(symbol, 0))
                    
                    if oi_qty <= 0:
                        continue
                    
                    try:
                        price = float(ticker.get('lastPrice', 0))
                        oi_value = oi_qty * price
                        volume_24h = float(ticker.get('quoteVolume', 0))
                        
                        change_5m, change_1h, change_24h = self.calculate_oi_change(
                            symbol, oi_value, current_time
                        )
                        
                        # Format symbol for display
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
                print(f"Binance error: {e}")
        
        self.last_update = current_time
        return results


class BinanceCoinExchange(BaseExchange):
    """Binance COIN-M Futures exchange integration."""
    
    name = "binance_coin"
    display_name = "Binance COIN-M"
    
    BASE_URL = "https://dapi.binance.com"
    
    async def fetch_oi_data(self) -> List[OIData]:
        """Fetch OI data from Binance COIN-M Futures."""
        results = []
        current_time = int(time.time())
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                ticker_resp = await client.get(f"{self.BASE_URL}/dapi/v1/ticker/24hr")
                tickers = ticker_resp.json()
                
                for ticker in tickers:
                    if not isinstance(ticker, dict):
                        continue
                    
                    symbol = ticker.get('symbol', '')
                    if not symbol:
                        continue
                    
                    try:
                        oi_resp = await client.get(
                            f"{self.BASE_URL}/dapi/v1/openInterest",
                            params={"symbol": symbol}
                        )
                        oi_data = oi_resp.json()
                        
                        if 'openInterest' not in oi_data:
                            continue
                        
                        price = float(ticker.get('lastPrice', 0))
                        oi_qty = float(oi_data.get('openInterest', 0))
                        oi_value = oi_qty * price
                        volume_24h = float(ticker.get('quoteVolume', 0))
                        
                        change_5m, change_1h, change_24h = self.calculate_oi_change(
                            symbol, oi_value, current_time
                        )
                        
                        results.append(OIData(
                            symbol=symbol,
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
                print(f"Binance COIN-M error: {e}")
        
        self.last_update = current_time
        return results
