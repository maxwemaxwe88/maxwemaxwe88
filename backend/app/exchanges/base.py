from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SymbolInfo:
    symbol: str
    volume_24h: float | None
    price: float | None


@dataclass(frozen=True)
class OIQuote:
    symbol: str
    oi: float
    price: float | None


class ExchangeConnector(Protocol):
    name: str

    async def list_top_symbols(self, limit: int) -> list[SymbolInfo]: ...

    async def fetch_open_interest(self, symbol: str) -> OIQuote: ...

