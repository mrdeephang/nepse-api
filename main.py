from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import logging

# Import models
from models.schemas import MarketSummaryResponse, StockDetailResponse

# Import scraper
from scraper.nepse_scraper import scraper, OptimalNepseScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("NEPSE API Starting...")
    print("🚀 NEPSE API Server Starting...")
    print("📊 Endpoints: /api/market/summary, /api/stock/{symbol}")
    print("📚 Documentation: http://localhost:8000")
    yield
    # Shutdown
    logger.info("NEPSE API Shutting down...")

# Initialize FastAPI
app = FastAPI(
    title="NEPSE Data API",
    description="API for Nepal Stock Exchange Data from ShareSansar",
    version="1.0.0",
    docs_url="/",
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

# Dependency for scraper
async def get_scraper():
    return scraper

# Exception handlers
@app.exception_handler(500)
async def internal_exception_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return {
        "success": False,
        "error": "Internal server error",
        "timestamp": datetime.now().isoformat()
    }

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "success": False,
        "error": "Endpoint not found",
        "timestamp": datetime.now().isoformat()
    }

# API Routes
@app.get(
    "/api/market/summary",
    response_model=MarketSummaryResponse,
    summary="Get Market Summary",
    description="Fetch NEPSE market summary including indices, turnover, and market data",
    response_description="Market summary and key indicators"
)
async def get_market_summary(scraper: OptimalNepseScraper = Depends(get_scraper)):
    """
    Get market summary and indices
    
    Returns comprehensive market summary:
    - NEPSE Index, Sensitive Index, Float Index
    - Total turnover
    - Market timestamp
    - Advance/Decline ratio
    """
    try:
        logger.info("Fetching market summary")
        data = await scraper.get_market_summary()
        if not data['success']:
            logger.error(f"Failed to fetch market summary: {data.get('error')}")
            raise HTTPException(status_code=500, detail=data['error'])
        
        logger.info("Successfully fetched market summary")
        return data
    except Exception as e:
        logger.error(f"Error in get_market_summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/api/stock/{symbol}",
    response_model=StockDetailResponse,
    summary="Get Stock Details",
    description="Fetch detailed information for a specific stock symbol",
    response_description="Detailed stock information"
)
async def get_stock_detail(
    symbol: str,
    scraper: OptimalNepseScraper = Depends(get_scraper)
):
    try:
        # Validate symbol
        if not symbol or len(symbol) < 2:
            raise HTTPException(status_code=400, detail="Invalid stock symbol")
        
        symbol_upper = symbol.upper()
        logger.info(f"Fetching stock details for: {symbol_upper}")
        
        data = await scraper.get_stock_detail(symbol_upper)
        if not data['success']:
            logger.warning(f"Stock not found: {symbol_upper}")
            raise HTTPException(status_code=404, detail=data['error'])
        
        logger.info(f"Successfully fetched details for: {symbol_upper}")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_stock_detail for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )