from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class MarketSummary(BaseModel):
    nepse_index: float = Field(..., description="NEPSE Index value")
    sensitive_index: float = Field(..., description="Sensitive Index value")
    float_index: float = Field(..., description="Float Index value")
    total_turnover: float = Field(..., description="Total turnover in Rs.")
    market_timestamp: str = Field(..., description="Market data timestamp")
    advances: int = Field(..., description="Number of advancing stocks")
    declines: int = Field(..., description="Number of declining stocks")
    unchanged: int = Field(..., description="Number of unchanged stocks")

class MarketSummaryResponse(BaseModel):
    success: bool = Field(..., description="Request success status")
    timestamp: datetime = Field(..., description="API response timestamp")
    data: MarketSummary = Field(..., description="Market summary data")

class StockDetailResponse(BaseModel):
    success: bool = Field(..., description="Request success status")
    timestamp: datetime = Field(..., description="API response timestamp")
    symbol: str = Field(..., description="Stock symbol")
    data: Dict[str, Any] = Field(..., description="Stock details")