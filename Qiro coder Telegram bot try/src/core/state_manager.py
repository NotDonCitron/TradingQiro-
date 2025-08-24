# feat(state): add SQLAlchemy async Base, Order/Position ORM and SessionFactory
from __future__ import annotations
import os
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from sqlalchemy import Column, String, DateTime, Numeric, JSON
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

Base = declarative_base()

def _now() -> datetime:
    return datetime.utcnow()

class Order(Base):
    __tablename__ = "orders"
    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: datetime = Column(DateTime, nullable=False, default=_now)
    broker_order_id: Optional[str] = Column(String(64), nullable=True, index=True)
    status: str = Column(String(32), nullable=False, default="PENDING", index=True)
    symbol: str = Column(String(32), nullable=False)
    side: str = Column(String(8), nullable=False)
    price: Optional[Decimal] = Column(Numeric(38, 18), nullable=True)
    quantity: Decimal = Column(Numeric(38, 18), nullable=False)
    filled_quantity: Decimal = Column(Numeric(38, 18), nullable=False, default=Decimal("0"))
    signal_metadata: Any = Column(JSON, nullable=True, default=dict)

class Position(Base):
    __tablename__ = "positions"
    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol: str = Column(String(32), nullable=False, unique=True)
    size: Decimal = Column(Numeric(38, 18), nullable=False, default=Decimal("0"))
    avg_price: Decimal = Column(Numeric(38, 18), nullable=False, default=Decimal("0"))
    updated_at: datetime = Column(DateTime, nullable=False, default=_now, onupdate=_now)

class StateManager:
    """Hält AsyncEngine und SessionFactory und kapselt einfache Operationen."""
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
        self.engine = create_async_engine(self.database_url, future=True, echo=False)
        self.Session = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    async def init_models(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def set_order_status(self, order_id: str, new_status: str, broker_order_id: Optional[str] = None) -> None:
        """Aktualisiert den Status einer Order."""
        async with self.Session() as session:
            order = await session.get(Order, order_id)
            if not order:
                raise ValueError(f"Order {order_id} not found")
            order.status = new_status
            if broker_order_id:
                order.broker_order_id = broker_order_id
            await session.commit()