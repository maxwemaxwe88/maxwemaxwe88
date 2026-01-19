import os
import requests
from dotenv import load_dotenv

load_dotenv()

class CoinglassAPI:
    BASE_URL = "https://open-api.coinglass.com/public/v2"

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("COINGLASS_API_KEY")
        if not self.api_key:
            # We will allow instantiation without key for testing if the user hasn't set it yet,
            # but methods will fail or warn.
            print("Warning: COINGLASS_API_KEY not found. API calls may fail.")
        
        self.headers = {
            "coinglassSecret": self.api_key if self.api_key else "",
            "accept": "application/json"
        }

    def get_open_interest(self, symbol):
        """
        Fetch Open Interest data for a specific symbol.
        Endpoint: /public/v2/open_interest
        """
        endpoint = "/open_interest"
        params = {'symbol': symbol}
        
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("code") == "0" and "data" in data:
                return data["data"]
            else:
                print(f"API Error: {data.get('msg', 'Unknown error')}")
                return None
        except requests.RequestException as e:
            print(f"Request Error: {e}")
            return None

    def get_supported_coins(self):
        # Fallback list of popular coins if we can't fetch them
        return ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "BNB", "LTC", "LINK", "MATIC"]
