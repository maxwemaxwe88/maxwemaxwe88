"""OI Screener - Main FastAPI Application."""
import asyncio
import time
from typing import Dict, List, Optional
from dataclasses import asdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.exchanges import EXCHANGES
from app.exchanges.base import BaseExchange, OIData


# Global state
exchange_instances: Dict[str, BaseExchange] = {}
cached_data: Dict[str, List[dict]] = {}
connected_clients: List[WebSocket] = []
update_task: Optional[asyncio.Task] = None


async def fetch_exchange_data(exchange_name: str, exchange: BaseExchange) -> List[dict]:
    """Fetch data from a single exchange."""
    try:
        data = await exchange.fetch_oi_data()
        return [asdict(d) for d in data]
    except Exception as e:
        print(f"Error fetching {exchange_name}: {e}")
        return []


async def update_all_exchanges():
    """Update data from all exchanges concurrently."""
    global cached_data
    
    tasks = []
    for name, exchange in exchange_instances.items():
        tasks.append((name, fetch_exchange_data(name, exchange)))
    
    for name, task in tasks:
        try:
            data = await task
            if data:
                cached_data[name] = data
        except Exception as e:
            print(f"Error updating {name}: {e}")


async def periodic_update():
    """Periodically update all exchange data."""
    while True:
        try:
            await update_all_exchanges()
            
            # Broadcast to connected WebSocket clients
            if connected_clients:
                message = {
                    "type": "update",
                    "data": cached_data,
                    "timestamp": int(time.time())
                }
                for client in connected_clients[:]:
                    try:
                        await client.send_json(message)
                    except Exception:
                        connected_clients.remove(client)
            
        except Exception as e:
            print(f"Periodic update error: {e}")
        
        await asyncio.sleep(10)  # Update every 10 seconds


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global exchange_instances, update_task
    
    # Initialize exchange instances
    for name, ExchangeClass in EXCHANGES.items():
        exchange_instances[name] = ExchangeClass()
    
    # Start periodic update task
    update_task = asyncio.create_task(periodic_update())
    
    yield
    
    # Cleanup
    if update_task:
        update_task.cancel()
        try:
            await update_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="OI Screener",
    description="Cryptocurrency Open Interest Screener",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Serve the main HTML page."""
    return FileResponse("static/index.html")


@app.get("/api/exchanges")
async def get_exchanges():
    """Get list of available exchanges."""
    return JSONResponse({
        "exchanges": [
            {"name": name, "display_name": ex.display_name}
            for name, ex in exchange_instances.items()
        ]
    })


@app.get("/api/oi")
async def get_all_oi():
    """Get OI data from all exchanges."""
    return JSONResponse({
        "data": cached_data,
        "timestamp": int(time.time())
    })


@app.get("/api/oi/{exchange}")
async def get_exchange_oi(exchange: str):
    """Get OI data from a specific exchange."""
    if exchange not in cached_data:
        return JSONResponse({"error": "Exchange not found"}, status_code=404)
    
    return JSONResponse({
        "exchange": exchange,
        "data": cached_data.get(exchange, []),
        "timestamp": int(time.time())
    })


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        # Send initial data
        await websocket.send_json({
            "type": "initial",
            "data": cached_data,
            "exchanges": [
                {"name": name, "display_name": ex.display_name}
                for name, ex in exchange_instances.items()
            ],
            "timestamp": int(time.time())
        })
        
        # Keep connection alive
        while True:
            try:
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                # Handle ping/pong
                if message == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send ping to keep alive
                await websocket.send_text("ping")
    
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
