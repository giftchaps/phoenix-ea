"""
Database Models
SQLAlchemy models for the Phoenix EA system
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class SymbolDB(Base):
    """Symbol database model"""
    __tablename__ = "symbols"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True, nullable=False)
    pip_size = Column(Float)
    tick_value = Column(Float)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SignalDB(Base):
    """Signal database model"""
    __tablename__ = "signals"
    
    id = Column(String(50), primary_key=True)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(5))
    side = Column(String(10))
    entry = Column(Float)
    stop_loss = Column(Float)
    take_profit_1 = Column(Float)
    take_profit_2 = Column(Float)
    take_profit_3 = Column(Float)
    confidence = Column(Float)
    sweep_type = Column(String(10))
    structure_type = Column(String(10))
    ob_present = Column(Boolean)
    premium_discount = Column(String(10))
    h4_aligned = Column(Boolean)
    h1_bias = Column(String(10))
    atr_percentile = Column(Float)
    posted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='pending')

class TradeDB(Base):
    """Trade database model"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True)
    signal_id = Column(String(50))
    entry_time = Column(DateTime)
    exit_time = Column(DateTime)
    entry_price = Column(Float)
    exit_price = Column(Float)
    lots = Column(Float)
    pnl_dollars = Column(Float)
    pnl_r = Column(Float)
    exit_reason = Column(String(20))
    mae_r = Column(Float)
    mfe_r = Column(Float)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://phoenix:phoenix123@localhost:5432/phoenix_ea")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
