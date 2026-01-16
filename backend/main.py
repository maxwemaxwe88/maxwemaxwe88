from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from backend.fetcher import screener

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the update loop in background
    task = asyncio.create_task(screener.update_loop())
    yield
    # Cleanup
    screener.running = False
    await screener.close()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/data")
async def get_data():
    return screener.get_all_data()

@app.get("/")
async def root():
    return {"message": "Crypto Screener API Running"}
