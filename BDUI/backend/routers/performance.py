from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from database import get_db
from models import PerformanceMetric
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/metrics")
async def get_performance_metrics(
    screen_id: Optional[int] = Query(None),
    operation_type: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    days: int = Query(7, le=30),
    db: Session = Depends(get_db)
):
    """
    Получить метрики производительности
    """
    query = db.query(PerformanceMetric)
    
    # Фильтр по экрану
    if screen_id:
        query = query.filter(PerformanceMetric.screen_id == screen_id)
    
    # Фильтр по типу операции
    if operation_type:
        query = query.filter(PerformanceMetric.operation_type == operation_type)
    
    # Фильтр по дате
    start_date = datetime.now() - timedelta(days=days)
    query = query.filter(PerformanceMetric.timestamp >= start_date)
    
    # Сортировка и лимит
    metrics = query.order_by(desc(PerformanceMetric.timestamp)).limit(limit).all()
    
    return {
        "metrics": [
            {
                "id": m.id,
                "screen_id": m.screen_id,
                "operation_type": m.operation_type,
                "total_time": m.total_time,
                "db_time": m.db_time,
                "backend_time": m.backend_time,
                "websocket_time": m.websocket_time,
                "client_time": m.client_time,
                "timestamp": m.timestamp.isoformat()
            }
            for m in metrics
        ],
        "count": len(metrics)
    }


@router.get("/metrics/stats")
async def get_performance_stats(
    screen_id: Optional[int] = Query(None),
    days: int = Query(7, le=30),
    db: Session = Depends(get_db)
):
    """
    Получить статистику производительности
    """
    query = db.query(PerformanceMetric)
    
    if screen_id:
        query = query.filter(PerformanceMetric.screen_id == screen_id)
    
    start_date = datetime.now() - timedelta(days=days)
    query = query.filter(PerformanceMetric.timestamp >= start_date)
    
    # Агрегированная статистика
    stats = query.with_entities(
        func.avg(PerformanceMetric.total_time).label('avg_total'),
        func.min(PerformanceMetric.total_time).label('min_total'),
        func.max(PerformanceMetric.total_time).label('max_total'),
        func.avg(PerformanceMetric.db_time).label('avg_db'),
        func.avg(PerformanceMetric.backend_time).label('avg_backend'),
        func.avg(PerformanceMetric.websocket_time).label('avg_websocket'),
        func.count(PerformanceMetric.id).label('total_operations')
    ).first()
    
    if not stats or stats.total_operations == 0:
        return {
            "avg_total_time": 0,
            "min_total_time": 0,
            "max_total_time": 0,
            "avg_db_time": 0,
            "avg_backend_time": 0,
            "avg_websocket_time": 0,
            "total_operations": 0
        }
    
    return {
        "avg_total_time": round(stats.avg_total, 2) if stats.avg_total else 0,
        "min_total_time": round(stats.min_total, 2) if stats.min_total else 0,
        "max_total_time": round(stats.max_total, 2) if stats.max_total else 0,
        "avg_db_time": round(stats.avg_db, 2) if stats.avg_db else 0,
        "avg_backend_time": round(stats.avg_backend, 2) if stats.avg_backend else 0,
        "avg_websocket_time": round(stats.avg_websocket, 2) if stats.avg_websocket else 0,
        "total_operations": stats.total_operations
    }


@router.get("/metrics/recent")
async def get_recent_metrics(
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    """
    Получить последние метрики производительности
    """
    metrics = db.query(PerformanceMetric)\
        .order_by(desc(PerformanceMetric.timestamp))\
        .limit(limit)\
        .all()
    
    return {
        "metrics": [
            {
                "screen_id": m.screen_id,
                "total_time": round(m.total_time, 2),
                "db_time": round(m.db_time, 2),
                "backend_time": round(m.backend_time, 2),
                "timestamp": m.timestamp.isoformat()
            }
            for m in metrics
        ]
    }

