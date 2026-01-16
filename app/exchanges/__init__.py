# Exchange integrations
from .binance import BinanceExchange
from .bybit import BybitExchange
from .okx import OKXExchange
from .bitget import BitgetExchange
from .gate import GateExchange
from .mexc import MEXCExchange
from .kucoin import KuCoinExchange
from .htx import HTXExchange
from .deribit import DeribitExchange
from .phemex import PhemexExchange

EXCHANGES = {
    "binance": BinanceExchange,
    "bybit": BybitExchange,
    "okx": OKXExchange,
    "bitget": BitgetExchange,
    "gate": GateExchange,
    "mexc": MEXCExchange,
    "kucoin": KuCoinExchange,
    "htx": HTXExchange,
    "deribit": DeribitExchange,
    "phemex": PhemexExchange,
}
