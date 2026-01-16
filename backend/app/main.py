from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api import router
from .collector import Collector
from .config import SETTINGS
from .db import init_db
from .exchanges.binance import BinanceUsdM
from .exchanges.bybit import BybitLinear
from .exchanges.okx import OkxSwap
from .http import make_session


def create_app() -> FastAPI:
    app = FastAPI(title="OI Screener", version="0.1.0")

    session = make_session(user_agent=SETTINGS.user_agent, timeout_seconds=SETTINGS.http_timeout_seconds)
    connectors = [BinanceUsdM(session), BybitLinear(session), OkxSwap(session)]
    collector = Collector(db_path=SETTINGS.db_path, connectors=connectors)

    @app.on_event("startup")
    async def _startup():
        await init_db(SETTINGS.db_path)
        collector.start()

    @app.on_event("shutdown")
    async def _shutdown():
        await collector.stop()
        await session.close()

    # API
    app.include_router(router, prefix="/api")

    # Static UI
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    # Dependency injection: FastAPI doesn't pass arbitrary deps to router handlers by default,
    # so we use a small override for endpoints that need collector.
    # We expose it via app.state.
    app.state.collector = collector

    return app


app = create_app()

