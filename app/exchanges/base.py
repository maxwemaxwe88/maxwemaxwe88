"""Base exchange class for OI data fetching."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass
import time


@dataclass
class OIData:
    """Open Interest data structure."""
    symbol: str
    price: float
    oi_value: float  # OI in USD
    oi_change_5m: float  # Percentage change
    oi_change_1h: float
    oi_change_24h: float
    volume_24h: float
    timestamp: int


class BaseExchange(ABC):
    """Base class for exchange integrations."""
    
    name: str = "base"
    display_name: str = "Base Exchange"
    
    def __init__(self):
        self.oi_history: Dict[str, List[tuple]] = {}  # symbol -> [(timestamp, oi_value), ...]
        self.last_update: float = 0
    
    @abstractmethod
    async def fetch_oi_data(self) -> List[OIData]:
        """Fetch current OI data for all futures symbols."""
        pass
    
    def calculate_oi_change(self, symbol: str, current_oi: float, current_time: int) -> tuple:
        """Calculate OI changes over different timeframes."""
        if symbol not in self.oi_history:
            self.oi_history[symbol] = []
        
        history = self.oi_history[symbol]
        
        # Add current data point
        history.append((current_time, current_oi))
        
        # Keep only last 24 hours of data
        cutoff = current_time - 86400
        self.oi_history[symbol] = [(t, v) for t, v in history if t > cutoff]
        history = self.oi_history[symbol]
        
        # Calculate changes
        change_5m = self._get_change(history, current_oi, current_time, 300)
        change_1h = self._get_change(history, current_oi, current_time, 3600)
        change_24h = self._get_change(history, current_oi, current_time, 86400)
        
        return change_5m, change_1h, change_24h
    
    def _get_change(self, history: List[tuple], current_oi: float, 
                    current_time: int, seconds: int) -> float:
        """Get percentage change from X seconds ago."""
        target_time = current_time - seconds
        
        # Find closest data point to target time
        closest = None
        min_diff = float('inf')
        
        for ts, oi in history:
            diff = abs(ts - target_time)
            if diff < min_diff:
                min_diff = diff
                closest = oi
        
        if closest and closest > 0:
            return ((current_oi - closest) / closest) * 100
        return 0.0
