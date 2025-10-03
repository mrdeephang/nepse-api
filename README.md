# NEPSE API

FastAPI service for Nepal Stock Exchange data with real-time scraping.

## Features

- Live market data
- Market summary
- Stock details
- Top gainers/losers
- Auto-generated Swagger docs

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Run
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Docs

Visit: http://localhost:8000

## Endpoints

- GET /api/market/live - Live data
- GET /api/market/summary - Market summary
- GET /api/stock/{symbol} - Stock details
- GET /api/market/top-gainers - Top gainers
- GET /api/market/top-losers - Top losers
