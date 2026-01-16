"""HyperLiquid DEX OI data fetcher."""
import httpx
import time
from typing import List
from .base import BaseExchange, OIData


class HyperLiquidExchange(BaseExchange):
    """HyperLiquid DEX integration."""
    
    name = "hyperliquid"
    display_name = "HyperLiquid"
    
    BASE_URL = "https://api.hyperliquid.xyz"
    
    async def fetch_oi_data(self) -> List[OIData]:
        """Fetch OI data from HyperLiquid."""
        results = []
        current_time = int(time.time())
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get meta info (asset list)
                meta_resp = await client.post(
                    f"{self.BASE_URL}/info",
                    json={"type": "meta"}
                )
                meta_data = meta_resp.json()
                
                universe = meta_data.get('universe', [])
                
                # Get all mids (prices)
                mids_resp = await client.post(
                    f"{self.BASE_URL}/info",
                    json={"type": "allMids"}
                )
                mids_data = mids_resp.json()
                
                # Get open interest
                for i, asset in enumerate(universe):
                    asset_name = asset.get('name', '')
                    
                    try:
                        # Get asset context for OI
                        ctx_resp = await client.post(
                            f"{self.BASE_URL}/info",
                            json={"type": "metaAndAssetCtxs"}
                        )
                        ctx_data = ctx_resp.json()
                        
                        asset_ctxs = ctx_data[1] if len(ctx_data) > 1 else []
                        
                        if i >= len(asset_ctxs):
                            continue
                        
                        asset_ctx = asset_ctxs[i]
                        
                        price = float(mids_data.get(asset_name, 0))
                        oi_value = float(asset_ctx.get('openInterest', 0)) * price
                        volume_24h = float(asset_ctx.get('dayNtlVlm', 0))
                        
                        if oi_value <= 0:
                            continue
                        
                        change_5m, change_1h, change_24h = self.calculate_oi_change(
                            asset_name, oi_value, current_time
                        )
                        
                        results.append(OIData(
                            symbol=asset_name,
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
                print(f"HyperLiquid error: {e}")
        
        self.last_update = current_time
        return results
