from __future__ import annotations

from pydantic import BaseModel


class Settings(BaseModel):
    db_path: str = "data/oi_snapshots.sqlite3"
    fetch_interval_seconds: int = 60
    max_symbols_per_exchange: int = 75
    http_timeout_seconds: int = 20
    user_agent: str = "oi-screener/0.1"


SETTINGS = Settings()

