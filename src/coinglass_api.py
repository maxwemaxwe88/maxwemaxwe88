"""
Coinglass API Client for fetching Open Interest and related data
"""
import requests
import time
from typing import Optional, Dict, List, Any
from .config import Config


class CoinglassAPIError(Exception):
    """Custom exception for Coinglass API errors"""
    pass


class CoinglassClient:
    """
    Client for interacting with Coinglass API
    
    Provides methods to fetch:
    - Open Interest data
    - Open Interest history
    - Funding rates
    - Liquidation data
    - Long/Short ratios
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Coinglass API client
        
        Args:
            api_key: Optional API key. If not provided, uses config value.
        """
        self.api_key = api_key or Config.COINGLASS_API_KEY
        self.base_url = Config.COINGLASS_BASE_URL
        self.public_url = Config.COINGLASS_PUBLIC_URL
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Setup session with default headers"""
        self.session.headers.update({
            "accept": "application/json",
            "Content-Type": "application/json"
        })
        if self.api_key:
            self.session.headers["CG-API-KEY"] = self.api_key
            self.session.headers["coinglassSecret"] = self.api_key
    
    def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict] = None,
        use_public: bool = False,
        retries: int = None
    ) -> Dict:
        """
        Make API request with retry logic
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            use_public: Use public API endpoint
            retries: Number of retries (default from config)
            
        Returns:
            API response data
        """
        retries = retries or Config.MAX_RETRIES
        base = self.public_url if use_public else self.base_url
        url = f"{base}/{endpoint}"
        
        last_error = None
        for attempt in range(retries):
            try:
                response = self.session.get(
                    url, 
                    params=params, 
                    timeout=Config.REQUEST_TIMEOUT
                )
                
                if response.status_code == 429:
                    # Rate limited, wait and retry
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                # Check for API-level errors
                if isinstance(data, dict):
                    if data.get("success") == False or data.get("code") not in [None, "0", 0]:
                        error_msg = data.get("msg") or data.get("message") or "Unknown API error"
                        raise CoinglassAPIError(f"API Error: {error_msg}")
                
                return data
                
            except requests.exceptions.RequestException as e:
                last_error = e
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                continue
        
        raise CoinglassAPIError(f"Request failed after {retries} attempts: {last_error}")
    
    # =====================
    # Open Interest Methods
    # =====================
    
    def get_open_interest_list(
        self, 
        exchange: Optional[str] = None,
        symbol: Optional[str] = None
    ) -> List[Dict]:
        """
        Get list of all coins with open interest data
        
        Args:
            exchange: Filter by exchange (e.g., "Binance")
            symbol: Filter by symbol (e.g., "BTC")
            
        Returns:
            List of open interest data for each coin
        """
        params = {}
        if exchange:
            params["ex"] = exchange
        if symbol:
            params["symbol"] = symbol
            
        data = self._make_request("open_interest", params)
        return data.get("data", []) if isinstance(data, dict) else data
    
    def get_aggregated_open_interest(self, symbol: str = "BTC") -> Dict:
        """
        Get aggregated open interest across all exchanges for a symbol
        
        Args:
            symbol: Coin symbol (e.g., "BTC", "ETH")
            
        Returns:
            Aggregated open interest data
        """
        params = {"symbol": symbol}
        data = self._make_request("open_interest", params)
        return data.get("data", {}) if isinstance(data, dict) else data
    
    def get_open_interest_history(
        self, 
        symbol: str = "BTC",
        interval: str = "h4",
        limit: int = 100
    ) -> List[Dict]:
        """
        Get historical open interest data
        
        Args:
            symbol: Coin symbol
            interval: Time interval (m1, m5, m15, h1, h4, h12, d1)
            limit: Number of data points
            
        Returns:
            Historical open interest data
        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        data = self._make_request("open_interest_history", params)
        return data.get("data", []) if isinstance(data, dict) else data
    
    def get_oi_ohlc(
        self, 
        exchange: str = "Binance",
        symbol: str = "BTCUSDT",
        interval: str = "h4",
        limit: int = 100
    ) -> List[Dict]:
        """
        Get Open Interest OHLC (candlestick) data
        
        Args:
            exchange: Exchange name
            symbol: Trading pair
            interval: Candle interval
            limit: Number of candles
            
        Returns:
            OHLC data for open interest
        """
        params = {
            "ex": exchange,
            "pair": symbol,
            "interval": interval,
            "limit": limit
        }
        data = self._make_request("open_interest_ohlc", params)
        return data.get("data", []) if isinstance(data, dict) else data
    
    # =====================
    # Funding Rate Methods
    # =====================
    
    def get_funding_rates(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get current funding rates across exchanges
        
        Args:
            symbol: Optional coin symbol filter
            
        Returns:
            List of funding rate data
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
            
        data = self._make_request("funding", params)
        return data.get("data", []) if isinstance(data, dict) else data
    
    def get_funding_rate_history(
        self, 
        exchange: str = "Binance",
        symbol: str = "BTCUSDT",
        limit: int = 100
    ) -> List[Dict]:
        """
        Get historical funding rates
        
        Args:
            exchange: Exchange name
            symbol: Trading pair
            limit: Number of data points
            
        Returns:
            Historical funding rate data
        """
        params = {
            "ex": exchange,
            "pair": symbol,
            "limit": limit
        }
        data = self._make_request("funding_history", params)
        return data.get("data", []) if isinstance(data, dict) else data
    
    # =====================
    # Liquidation Methods
    # =====================
    
    def get_liquidation_data(
        self, 
        symbol: Optional[str] = None,
        time_type: int = 2  # 0=all, 1=1h, 2=4h, 3=12h, 4=24h
    ) -> List[Dict]:
        """
        Get liquidation data
        
        Args:
            symbol: Optional coin symbol filter
            time_type: Time range (0=all, 1=1h, 2=4h, 3=12h, 4=24h)
            
        Returns:
            Liquidation data
        """
        params = {"time_type": time_type}
        if symbol:
            params["symbol"] = symbol
            
        data = self._make_request("liquidation", params)
        return data.get("data", []) if isinstance(data, dict) else data
    
    def get_liquidation_history(
        self,
        symbol: str = "BTC",
        interval: str = "h4",
        limit: int = 100
    ) -> List[Dict]:
        """
        Get historical liquidation data
        
        Args:
            symbol: Coin symbol
            interval: Time interval
            limit: Number of data points
            
        Returns:
            Historical liquidation data
        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        data = self._make_request("liquidation_history", params)
        return data.get("data", []) if isinstance(data, dict) else data
    
    # =====================
    # Long/Short Ratio Methods
    # =====================
    
    def get_long_short_ratio(
        self, 
        symbol: str = "BTC",
        interval: str = "h4",
        limit: int = 100
    ) -> List[Dict]:
        """
        Get long/short ratio data
        
        Args:
            symbol: Coin symbol
            interval: Time interval
            limit: Number of data points
            
        Returns:
            Long/short ratio data
        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        data = self._make_request("long_short", params)
        return data.get("data", []) if isinstance(data, dict) else data
    
    def get_top_long_short_ratio(
        self, 
        exchange: str = "Binance",
        symbol: str = "BTCUSDT",
        interval: str = "h4",
        limit: int = 100
    ) -> List[Dict]:
        """
        Get top traders long/short ratio
        
        Args:
            exchange: Exchange name
            symbol: Trading pair
            interval: Time interval
            limit: Number of data points
            
        Returns:
            Top traders long/short ratio data
        """
        params = {
            "ex": exchange,
            "pair": symbol,
            "interval": interval,
            "limit": limit
        }
        data = self._make_request("top_long_short_position_ratio", params)
        return data.get("data", []) if isinstance(data, dict) else data
    
    # =====================
    # Market Data Methods
    # =====================
    
    def get_coin_list(self) -> List[Dict]:
        """
        Get list of all supported coins
        
        Returns:
            List of coins with basic info
        """
        data = self._make_request("coins", use_public=False)
        return data.get("data", []) if isinstance(data, dict) else data
    
    def get_exchange_list(self) -> List[str]:
        """
        Get list of supported exchanges
        
        Returns:
            List of exchange names
        """
        return Config.SUPPORTED_EXCHANGES
    
    def get_global_long_short(self) -> Dict:
        """
        Get global long/short ratio for the entire market
        
        Returns:
            Global long/short statistics
        """
        data = self._make_request("global_long_short", use_public=False)
        return data.get("data", {}) if isinstance(data, dict) else data
    
    # =====================
    # Convenience Methods
    # =====================
    
    def get_market_overview(self) -> Dict[str, Any]:
        """
        Get a comprehensive market overview including OI, funding, and liquidations
        
        Returns:
            Dictionary with market overview data
        """
        overview = {
            "open_interest": [],
            "funding_rates": [],
            "liquidations": []
        }
        
        try:
            overview["open_interest"] = self.get_open_interest_list()
        except CoinglassAPIError:
            pass
            
        try:
            overview["funding_rates"] = self.get_funding_rates()
        except CoinglassAPIError:
            pass
            
        try:
            overview["liquidations"] = self.get_liquidation_data()
        except CoinglassAPIError:
            pass
            
        return overview
    
    def health_check(self) -> bool:
        """
        Check if API is accessible
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            self.get_open_interest_list(symbol="BTC")
            return True
        except Exception:
            return False
