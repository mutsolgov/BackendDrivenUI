from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import redis
from database import engine, get_db
from models import Base
from routers import screens, components, analytics, ab_testing, templates, performance
from cache import redis_client
from websocket_manager import manager
from init_screens import init_screens_from_json


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    
    print("\n" + "="*60)
    print("🚀 Инициализация BDUI Framework")
    print("="*60)
    init_screens_from_json()
    print("="*60 + "\n")
    
    yield


app = FastAPI(
    title="BDUI Framework API",
    description="Backend Driven UI Framework for Avito",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(screens.router, prefix="/api/screens", tags=["screens"])
app.include_router(components.router, prefix="/api/components", tags=["components"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(ab_testing.router, prefix="/api/ab-testing", tags=["ab-testing"])
app.include_router(templates.router, prefix="/api/templates", tags=["templates"])
app.include_router(performance.router, prefix="/api/performance", tags=["performance"])

@app.websocket("/ws/screen/{screen_id}")
async def websocket_screen(websocket: WebSocket, screen_id: str):
    await manager.websocket_endpoint(websocket, screen_id, is_admin=False)

@app.websocket("/ws/admin")
async def websocket_admin(websocket: WebSocket):
    await manager.websocket_endpoint(websocket, is_admin=True)


@app.get("/")
async def root():
    return {"message": "BDUI Framework API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    try:
        redis_client.ping()
        return {"status": "healthy", "database": "connected", "cache": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}





