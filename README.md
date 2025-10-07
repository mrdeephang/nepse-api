# NEPSE API

FastAPI service for Nepal Stock Exchange data with real-time scraping.

## Features

- Market summary
- Stock details by symbol
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

- GET /api/market/summary - Market summary
- GET /api/stock/{symbol} - Stock details
