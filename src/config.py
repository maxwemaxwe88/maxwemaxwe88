"""
Configuration module for Coinglass Open Interest Screener
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for the screener"""
    
    # Coinglass API settings
    COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY", "")
    COINGLASS_BASE_URL = "https://open-api.coinglass.com/public/v2"
    
    # Alternative endpoints (public, no API key required for some)
    COINGLASS_PUBLIC_URL = "https://open-api-v3.coinglass.com/api"
    
    # Default settings
    DEFAULT_EXCHANGE = os.getenv("DEFAULT_EXCHANGE", "all")
    DEFAULT_LIMIT = int(os.getenv("DEFAULT_LIMIT", "50"))
    
    # Supported exchanges
    SUPPORTED_EXCHANGES = [
        "Binance", "OKX", "Bybit", "Bitget", "dYdX", 
        "Huobi", "Gate", "CoinEx", "Kraken", "Bitmex"
    ]
    
    # Request settings
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    
    @classmethod
    def get_headers(cls) -> dict:
        """Get API request headers"""
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        if cls.COINGLASS_API_KEY:
            headers["CG-API-KEY"] = cls.COINGLASS_API_KEY
            headers["coinglassSecret"] = cls.COINGLASS_API_KEY
        return headers
    
    @classmethod
    def is_api_key_set(cls) -> bool:
        """Check if API key is configured"""
        return bool(cls.COINGLASS_API_KEY and cls.COINGLASS_API_KEY != "your_api_key_here")
