"""
Open Interest Screener - Main screening and filtering logic
"""
import pandas as pd
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from .coinglass_api import CoinglassClient, CoinglassAPIError


class SortBy(Enum):
    """Sorting options for screener results"""
    OI_VALUE = "oi_value"
    OI_CHANGE_1H = "oi_change_1h"
    OI_CHANGE_4H = "oi_change_4h"
    OI_CHANGE_24H = "oi_change_24h"
    PRICE = "price"
    PRICE_CHANGE_24H = "price_change_24h"
    VOLUME_24H = "volume_24h"
    SYMBOL = "symbol"


class FilterType(Enum):
    """Filter types for screening"""
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    EQUALS = "eq"
    BETWEEN = "between"


@dataclass
class ScreenerFilter:
    """Definition of a screener filter"""
    field: str
    filter_type: FilterType
    value: Any
    value2: Optional[Any] = None  # For BETWEEN filter


@dataclass
class ScreenerResult:
    """Container for screener results"""
    data: pd.DataFrame
    total_count: int
    filtered_count: int
    timestamp: str
    filters_applied: List[str]


class OpenInterestScreener:
    """
    Open Interest Screener for cryptocurrency derivatives markets
    
    Provides:
    - Real-time OI data screening
    - Multiple filter combinations
    - Sorting and ranking
    - Change detection (1h, 4h, 24h)
    - Exchange-specific filtering
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the screener
        
        Args:
            api_key: Optional Coinglass API key
        """
        self.client = CoinglassClient(api_key)
        self._cache = {}
        self._cache_ttl = 60  # Cache TTL in seconds
    
    def fetch_oi_data(
        self, 
        exchange: Optional[str] = None,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """
        Fetch open interest data and convert to DataFrame
        
        Args:
            exchange: Optional exchange filter
            force_refresh: Force refresh even if cached
            
        Returns:
            DataFrame with OI data
        """
        try:
            raw_data = self.client.get_open_interest_list(exchange=exchange)
            
            if not raw_data:
                return pd.DataFrame()
            
            # Normalize data structure
            records = []
            for item in raw_data:
                record = self._normalize_oi_record(item)
                if record:
                    records.append(record)
            
            if not records:
                return pd.DataFrame()
                
            df = pd.DataFrame(records)
            return df
            
        except CoinglassAPIError as e:
            print(f"API Error: {e}")
            return pd.DataFrame()
    
    def _normalize_oi_record(self, item: Dict) -> Optional[Dict]:
        """
        Normalize OI record to consistent format
        
        Args:
            item: Raw API response item
            
        Returns:
            Normalized record dictionary
        """
        try:
            # Handle different API response formats
            symbol = item.get("symbol") or item.get("coin") or item.get("s", "")
            
            record = {
                "symbol": symbol.upper(),
                "oi_value": self._safe_float(item.get("openInterest") or item.get("oi") or item.get("openInterestAmount", 0)),
                "oi_value_usd": self._safe_float(item.get("openInterestUsd") or item.get("oiUsd", 0)),
                "oi_change_1h": self._safe_float(item.get("h1OiChangePercent") or item.get("oi1hChange", 0)),
                "oi_change_4h": self._safe_float(item.get("h4OiChangePercent") or item.get("oi4hChange", 0)),
                "oi_change_24h": self._safe_float(item.get("h24OiChangePercent") or item.get("oi24hChange", 0)),
                "price": self._safe_float(item.get("price") or item.get("lastPrice", 0)),
                "price_change_24h": self._safe_float(item.get("priceChangePercent") or item.get("price24hChange", 0)),
                "volume_24h": self._safe_float(item.get("volUsd") or item.get("volume24h", 0)),
                "exchange": item.get("exchange") or item.get("exchangeName", "Aggregated"),
                "market_cap": self._safe_float(item.get("marketCap", 0)),
                "avg_funding_rate": self._safe_float(item.get("avgFundingRate", 0)),
            }
            
            # Calculate additional metrics
            if record["oi_value_usd"] > 0:
                record["oi_volume_ratio"] = record["volume_24h"] / record["oi_value_usd"] if record["volume_24h"] else 0
            else:
                record["oi_volume_ratio"] = 0
                
            return record
            
        except Exception:
            return None
    
    def _safe_float(self, value: Any) -> float:
        """Safely convert value to float"""
        if value is None:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def screen(
        self,
        filters: Optional[List[ScreenerFilter]] = None,
        sort_by: SortBy = SortBy.OI_VALUE,
        ascending: bool = False,
        limit: int = 50,
        exchange: Optional[str] = None,
        min_oi_usd: float = 0,
        min_volume: float = 0
    ) -> ScreenerResult:
        """
        Screen coins based on open interest criteria
        
        Args:
            filters: List of ScreenerFilter objects
            sort_by: Field to sort by
            ascending: Sort order
            limit: Maximum number of results
            exchange: Optional exchange filter
            min_oi_usd: Minimum OI in USD
            min_volume: Minimum 24h volume
            
        Returns:
            ScreenerResult with filtered data
        """
        import datetime
        
        # Fetch data
        df = self.fetch_oi_data(exchange=exchange)
        
        if df.empty:
            return ScreenerResult(
                data=pd.DataFrame(),
                total_count=0,
                filtered_count=0,
                timestamp=datetime.datetime.now().isoformat(),
                filters_applied=[]
            )
        
        total_count = len(df)
        filters_applied = []
        
        # Apply minimum OI filter
        if min_oi_usd > 0:
            df = df[df["oi_value_usd"] >= min_oi_usd]
            filters_applied.append(f"OI >= ${min_oi_usd:,.0f}")
        
        # Apply minimum volume filter
        if min_volume > 0:
            df = df[df["volume_24h"] >= min_volume]
            filters_applied.append(f"Volume >= ${min_volume:,.0f}")
        
        # Apply custom filters
        if filters:
            for f in filters:
                df = self._apply_filter(df, f)
                filters_applied.append(f"{f.field} {f.filter_type.value} {f.value}")
        
        # Sort
        sort_column = sort_by.value
        if sort_column in df.columns:
            df = df.sort_values(by=sort_column, ascending=ascending)
        
        # Limit results
        df = df.head(limit)
        
        return ScreenerResult(
            data=df,
            total_count=total_count,
            filtered_count=len(df),
            timestamp=datetime.datetime.now().isoformat(),
            filters_applied=filters_applied
        )
    
    def _apply_filter(self, df: pd.DataFrame, f: ScreenerFilter) -> pd.DataFrame:
        """Apply a single filter to the DataFrame"""
        if f.field not in df.columns:
            return df
            
        if f.filter_type == FilterType.GREATER_THAN:
            return df[df[f.field] > f.value]
        elif f.filter_type == FilterType.LESS_THAN:
            return df[df[f.field] < f.value]
        elif f.filter_type == FilterType.EQUALS:
            return df[df[f.field] == f.value]
        elif f.filter_type == FilterType.BETWEEN:
            return df[(df[f.field] >= f.value) & (df[f.field] <= f.value2)]
        
        return df
    
    # =====================
    # Preset Screens
    # =====================
    
    def get_top_oi_gainers(
        self, 
        timeframe: str = "24h",
        limit: int = 20,
        min_oi_usd: float = 1_000_000
    ) -> ScreenerResult:
        """
        Get coins with highest OI increase
        
        Args:
            timeframe: 1h, 4h, or 24h
            limit: Number of results
            min_oi_usd: Minimum OI in USD
            
        Returns:
            ScreenerResult with top gainers
        """
        sort_map = {
            "1h": SortBy.OI_CHANGE_1H,
            "4h": SortBy.OI_CHANGE_4H,
            "24h": SortBy.OI_CHANGE_24H
        }
        
        sort_by = sort_map.get(timeframe, SortBy.OI_CHANGE_24H)
        
        filters = [
            ScreenerFilter(
                field=sort_by.value,
                filter_type=FilterType.GREATER_THAN,
                value=0
            )
        ]
        
        return self.screen(
            filters=filters,
            sort_by=sort_by,
            ascending=False,
            limit=limit,
            min_oi_usd=min_oi_usd
        )
    
    def get_top_oi_losers(
        self, 
        timeframe: str = "24h",
        limit: int = 20,
        min_oi_usd: float = 1_000_000
    ) -> ScreenerResult:
        """
        Get coins with highest OI decrease
        
        Args:
            timeframe: 1h, 4h, or 24h
            limit: Number of results
            min_oi_usd: Minimum OI in USD
            
        Returns:
            ScreenerResult with top losers
        """
        sort_map = {
            "1h": SortBy.OI_CHANGE_1H,
            "4h": SortBy.OI_CHANGE_4H,
            "24h": SortBy.OI_CHANGE_24H
        }
        
        sort_by = sort_map.get(timeframe, SortBy.OI_CHANGE_24H)
        
        filters = [
            ScreenerFilter(
                field=sort_by.value,
                filter_type=FilterType.LESS_THAN,
                value=0
            )
        ]
        
        return self.screen(
            filters=filters,
            sort_by=sort_by,
            ascending=True,
            limit=limit,
            min_oi_usd=min_oi_usd
        )
    
    def get_high_oi_volume_ratio(
        self, 
        limit: int = 20,
        min_oi_usd: float = 1_000_000
    ) -> ScreenerResult:
        """
        Get coins with high OI to volume ratio
        (potential for volatility)
        
        Args:
            limit: Number of results
            min_oi_usd: Minimum OI in USD
            
        Returns:
            ScreenerResult with high ratio coins
        """
        result = self.screen(
            sort_by=SortBy.OI_VALUE,
            ascending=False,
            limit=limit * 2,
            min_oi_usd=min_oi_usd
        )
        
        if not result.data.empty:
            result.data = result.data.sort_values(
                by="oi_volume_ratio", 
                ascending=False
            ).head(limit)
        
        return result
    
    def get_unusual_activity(
        self, 
        oi_change_threshold: float = 5.0,
        limit: int = 20,
        min_oi_usd: float = 500_000
    ) -> ScreenerResult:
        """
        Get coins with unusual OI activity
        (significant changes in short timeframes)
        
        Args:
            oi_change_threshold: Minimum absolute OI change %
            limit: Number of results
            min_oi_usd: Minimum OI in USD
            
        Returns:
            ScreenerResult with unusual activity
        """
        result = self.screen(
            limit=limit * 3,
            min_oi_usd=min_oi_usd
        )
        
        if not result.data.empty:
            df = result.data
            # Filter for unusual activity (high absolute change)
            df = df[
                (abs(df["oi_change_1h"]) >= oi_change_threshold) |
                (abs(df["oi_change_4h"]) >= oi_change_threshold * 1.5)
            ]
            df = df.head(limit)
            result.data = df
            result.filtered_count = len(df)
        
        return result
    
    def get_divergence_signals(
        self, 
        limit: int = 20,
        min_oi_usd: float = 1_000_000
    ) -> ScreenerResult:
        """
        Get coins where OI and price are diverging
        (potential trend reversal signals)
        
        Args:
            limit: Number of results
            min_oi_usd: Minimum OI in USD
            
        Returns:
            ScreenerResult with divergence signals
        """
        result = self.screen(
            limit=limit * 3,
            min_oi_usd=min_oi_usd
        )
        
        if not result.data.empty:
            df = result.data
            
            # Bullish divergence: Price down, OI up
            bullish = df[(df["price_change_24h"] < -2) & (df["oi_change_24h"] > 3)]
            bullish = bullish.copy()
            bullish["signal"] = "BULLISH"
            
            # Bearish divergence: Price up, OI down
            bearish = df[(df["price_change_24h"] > 2) & (df["oi_change_24h"] < -3)]
            bearish = bearish.copy()
            bearish["signal"] = "BEARISH"
            
            combined = pd.concat([bullish, bearish])
            combined = combined.sort_values(
                by="oi_value_usd", 
                ascending=False
            ).head(limit)
            
            result.data = combined
            result.filtered_count = len(combined)
        
        return result
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for the entire market
        
        Returns:
            Dictionary with market summary
        """
        result = self.screen(limit=1000, min_oi_usd=100_000)
        
        if result.data.empty:
            return {}
        
        df = result.data
        
        return {
            "total_coins": len(df),
            "total_oi_usd": df["oi_value_usd"].sum(),
            "avg_oi_change_1h": df["oi_change_1h"].mean(),
            "avg_oi_change_4h": df["oi_change_4h"].mean(),
            "avg_oi_change_24h": df["oi_change_24h"].mean(),
            "coins_with_rising_oi": len(df[df["oi_change_24h"] > 0]),
            "coins_with_falling_oi": len(df[df["oi_change_24h"] < 0]),
            "top_oi_coin": df.iloc[0]["symbol"] if len(df) > 0 else "N/A",
            "biggest_oi_gainer": df.loc[df["oi_change_24h"].idxmax()]["symbol"] if len(df) > 0 else "N/A",
            "biggest_oi_loser": df.loc[df["oi_change_24h"].idxmin()]["symbol"] if len(df) > 0 else "N/A",
        }
    
    def format_results(
        self, 
        result: ScreenerResult,
        format_type: str = "table"
    ) -> str:
        """
        Format screener results for display
        
        Args:
            result: ScreenerResult to format
            format_type: Output format (table, csv, json)
            
        Returns:
            Formatted string
        """
        if result.data.empty:
            return "No data available"
        
        df = result.data.copy()
        
        # Format numeric columns for display
        if "oi_value_usd" in df.columns:
            df["oi_value_usd"] = df["oi_value_usd"].apply(lambda x: f"${x:,.0f}")
        if "volume_24h" in df.columns:
            df["volume_24h"] = df["volume_24h"].apply(lambda x: f"${x:,.0f}")
        if "price" in df.columns:
            df["price"] = df["price"].apply(lambda x: f"${x:,.4f}" if x < 1 else f"${x:,.2f}")
        
        # Format percentage columns
        for col in ["oi_change_1h", "oi_change_4h", "oi_change_24h", "price_change_24h"]:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: f"{x:+.2f}%")
        
        if format_type == "csv":
            return df.to_csv(index=False)
        elif format_type == "json":
            return df.to_json(orient="records", indent=2)
        else:
            from tabulate import tabulate
            return tabulate(df, headers="keys", tablefmt="grid", showindex=False)
