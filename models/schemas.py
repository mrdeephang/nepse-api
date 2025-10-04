from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class StockData(BaseModel):
    symbol: str = Field(..., description="Stock symbol")
    company_name: str = Field(..., description="Company name")
    open_price: float = Field(..., description="Opening price")
    high_price: float = Field(..., description="High price")
    low_price: float = Field(..., description="Low price")
    close_price: float = Field(..., description="Closing price")
    volume: int = Field(..., description="Trading volume")
    change: float = Field(..., description="Price change")
    change_percent: float = Field(..., description="Percentage change")

class AdvanceDecline(BaseModel):
    advances: int = Field(..., description="Number of advancing stocks")
    declines: int = Field(..., description="Number of declining stocks")
    unchanged: int = Field(..., description="Number of unchanged stocks")

class MarketSummary(BaseModel):
    nepse_index: float = Field(..., description="NEPSE Index value")
    sensitive_index: Optional[float] = Field(None, description="Sensitive Index")
    float_index: Optional[float] = Field(None, description="Float Index")
    total_turnover: float = Field(..., description="Total turnover")
    total_volume: int = Field(..., description="Total volume")
    total_trades: int = Field(..., description="Total number of trades")
    advance_decline: AdvanceDecline = Field(..., description="Advance/Decline ratio")

class LiveMarketResponse(BaseModel):
    success: bool = Field(..., description="Request success status")
    timestamp: datetime = Field(..., description="Data timestamp")
    data: List[StockData] = Field(..., description="List of stock data")
    count: int = Field(..., description="Number of records")

class MarketSummaryResponse(BaseModel):
    success: bool = Field(..., description="Request success status")
    timestamp: datetime = Field(..., description="Data timestamp")
    data: MarketSummary = Field(..., description="Market summary data")

class StockDetailResponse(BaseModel):
    success: bool = Field(..., description="Request success status")
    timestamp: datetime = Field(..., description="Data timestamp")
    symbol: str = Field(..., description="Stock symbol")
    data: Dict[str, Any] = Field(..., description="Stock details")

class ErrorResponse(BaseModel):
    success: bool = Field(False, description="Request success status")
    error: str = Field(..., description="Error message")
    timestamp: datetime = Field(..., description="Error timestamp")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current timestamp")
    service: str = Field(..., description="Service name")