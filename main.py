from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional
import logging
from utils.helpers import cache_manager
# Import models
from models.schemas import (
    LiveMarketResponse, MarketSummaryResponse, StockDetailResponse, 
    ErrorResponse, HealthResponse
)

# Import scraper and utilities
from scraper.nepse_scraper import scraper, OptimalNepseScraper
from utils.helpers import prepare_response, validate_symbol, rate_limiter, cache_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("NEPSE API Starting...")
    print("🚀 NEPSE API Server Starting...")
    print("📊 Endpoints: /api/market/live, /api/market/summary, /api/stock/{symbol}")
    print("📚 Documentation: http://localhost:8000")
    yield
    # Shutdown
    logger.info("NEPSE API Shutting down...")
    print("👋 NEPSE API Server Shutting down...")

# Initialize FastAPI with optimal settings
app = FastAPI(
    title="NEPSE Data API",
    description="High-performance API for Nepal Stock Exchange Data with real-time scraping capabilities",
    version="2.0.0",
    docs_url="/",
    redoc_url="/docs",
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
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "Endpoint not found",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": str(exc.detail),
            "timestamp": datetime.now().isoformat()
        }
    )

# API Routes
@app.get(
    "/api/market/live",
    response_model=LiveMarketResponse,
    summary="Get Live Market Data",
    description="Fetch real-time NEPSE market data with all listed stocks including prices, volume, and changes",
    response_description="List of all stocks with current trading data"
)
async def get_live_market(scraper: OptimalNepseScraper = Depends(get_scraper)):
    """
    Get live NEPSE market data
    
    Returns complete market data including:
    - Stock symbols and company names
    - Opening, high, low, and closing prices
    - Trading volume
    - Price changes and percentages
    """
    try:
        logger.info("Fetching live market data")
        data = await scraper.get_live_market_data()
        if not data['success']:
            logger.error(f"Failed to fetch market data: {data.get('error')}")
            raise HTTPException(status_code=500, detail=data['error'])
        
        logger.info(f"Successfully fetched {data['count']} stocks")
        return prepare_response(data)
    except Exception as e:
        logger.error(f"Error in get_live_market: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/api/market/summary",
    response_model=MarketSummaryResponse,
    summary="Get Market Summary",
    description="Fetch NEPSE market summary including indices, turnover, volume, and advance/decline ratio",
    response_description="Market summary and key indicators"
)
async def get_market_summary(scraper: OptimalNepseScraper = Depends(get_scraper)):
    """
    Get market summary and indices
    
    Returns comprehensive market summary:
    - NEPSE Index, Sensitive Index, Float Index
    - Total turnover and trading volume
    - Number of trades
    - Advance/Decline ratio
    """
    try:
        logger.info("Fetching market summary")
        data = await scraper.get_market_summary()
        if not data['success']:
            logger.error(f"Failed to fetch market summary: {data.get('error')}")
            raise HTTPException(status_code=500, detail=data['error'])
        
        logger.info("Successfully fetched market summary")
        return prepare_response(data)
    except Exception as e:
        logger.error(f"Error in get_market_summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/api/stock/{symbol}",
    response_model=StockDetailResponse,
    summary="Get Stock Details",
    description="Fetch detailed information for a specific stock symbol including price data and company information",
    response_description="Detailed stock information"
)
async def get_stock_detail(
    symbol: str,
    scraper: OptimalNepseScraper = Depends(get_scraper)
):
    """
    Get detailed information for specific stock
    
    Parameters:
    - symbol: Stock symbol (e.g., 'NABIL', 'SCB', 'NTC')
    
    Returns detailed stock information:
    - Basic price data (open, high, low, close)
    - Trading volume and changes
    - Additional details like sector, market cap, P/E ratio
    """
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
        return prepare_response(data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_stock_detail for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/api/market/top-gainers",
    response_model=LiveMarketResponse,
    summary="Get Top Gainers",
    description="Fetch top gaining stocks by percentage change",
    response_description="List of top gaining stocks"
)
async def get_top_gainers(
    limit: int = Query(10, ge=1, le=50, description="Number of top gainers to return (1-50)"),
    scraper: OptimalNepseScraper = Depends(get_scraper)
):
    """
    Get top gaining stocks
    
    Parameters:
    - limit: Number of top gainers to return (default: 10, max: 50)
    
    Returns list of stocks with highest positive percentage change
    """
    try:
        logger.info(f"Fetching top {limit} gainers")
        data = await scraper.get_top_gainers(limit)
        if not data['success']:
            raise HTTPException(status_code=500, detail=data['error'])
        
        logger.info(f"Successfully fetched {len(data['data'])} gainers")
        return prepare_response(data)
    except Exception as e:
        logger.error(f"Error in get_top_gainers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/api/market/top-losers",
    response_model=LiveMarketResponse,
    summary="Get Top Losers",
    description="Fetch top losing stocks by percentage change",
    response_description="List of top losing stocks"
)
async def get_top_losers(
    limit: int = Query(10, ge=1, le=50, description="Number of top losers to return (1-50)"),
    scraper: OptimalNepseScraper = Depends(get_scraper)
):
    """
    Get top losing stocks
    
    Parameters:
    - limit: Number of top losers to return (default: 10, max: 50)
    
    Returns list of stocks with highest negative percentage change
    """
    try:
        logger.info(f"Fetching top {limit} losers")
        data = await scraper.get_top_losers(limit)
        if not data['success']:
            raise HTTPException(status_code=500, detail=data['error'])
        
        logger.info(f"Successfully fetched {len(data['data'])} losers")
        return prepare_response(data)
    except Exception as e:
        logger.error(f"Error in get_top_losers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/api/market/performance",
    summary="Get Market Performance",
    description="Get overall market performance metrics and statistics",
    response_description="Market performance metrics"
)
async def get_market_performance(scraper: OptimalNepseScraper = Depends(get_scraper)):
    """
    Get market performance metrics
    
    Returns comprehensive performance data:
    - Total number of stocks
    - Average change percentage
    - Count of gainers and losers
    - Top gainer and loser
    - Total market capitalization
    """
    try:
        logger.info("Fetching market performance")
        market_data = await scraper.get_live_market_data()
        
        if not market_data['success']:
            raise HTTPException(status_code=500, detail=market_data['error'])
        
        from utils.helpers import calculate_performance
        performance = calculate_performance(market_data['data'])
        
        response_data = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'data': performance
        }
        
        logger.info("Successfully calculated market performance")
        return prepare_response(response_data)
    except Exception as e:
        logger.error(f"Error in get_market_performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "NEPSE API",
        "version": "2.0.0"
    }

@app.get("/cache/clear")
async def clear_cache():
    """Clear all cached data (development endpoint)"""
    try:
        cache_manager.clear()
        logger.info("Cache cleared manually")
        return {
            "success": True,
            "message": "Cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cache/status")
async def cache_status():
    """Get cache status (development endpoint)"""
    try:
        cache_keys = list(cache_manager.cache.keys())
        return {
            "success": True,
            "cache_entries": len(cache_keys),
            "cache_keys": cache_keys,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting cache status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "🚀 NEPSE Data API",
        "description": "High-performance API for Nepal Stock Exchange Data",
        "version": "2.0.0",
        "endpoints": {
            "market_data": "/api/market/live",
            "market_summary": "/api/market/summary", 
            "stock_details": "/api/stock/{symbol}",
            "top_gainers": "/api/market/top-gainers",
            "top_losers": "/api/market/top-losers",
            "performance": "/api/market/performance",
            "health": "/health",
            "documentation": "/"
        },
        "examples": {
            "live_data": "GET /api/market/live",
            "stock_info": "GET /api/stock/NABIL",
            "top_5_gainers": "GET /api/market/top-gainers?limit=5"
        }
    }

@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "api": "NEPSE Data API",
        "version": "2.0.0",
        "status": "operational",
        "features": [
            "Real-time market data scraping",
            "Market summary and indices",
            "Individual stock details", 
            "Top gainers/losers",
            "Market performance metrics",
            "Caching for performance",
            "Rate limiting",
            "RESTful API design"
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/debug/raw-data")
async def debug_raw_data(scraper: OptimalNepseScraper = Depends(get_scraper)):
    """Debug endpoint to see raw data structure"""
    try:
        data = await scraper.get_live_market_data()
        return data
    except Exception as e:
        logger.error(f"Debug endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1,
        access_log=True,
        log_level="info"
    )