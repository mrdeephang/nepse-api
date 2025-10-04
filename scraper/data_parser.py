import re
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

class DataParser:
    def __init__(self):
        self.stock_patterns = {
            'symbol': r'[A-Z]{2,6}',
            'numeric': r'[+-]?\d*\.?\d+',
            'volume': r'\d{1,3}(?:,\d{3})*'
        }

    def clean_numeric_value(self, value: str) -> float:
        """Clean and convert numeric values from NEPSE data"""
        if not value or value.strip() in ['-', '--', '']:
            return 0.0
        
        try:
            # Remove commas, spaces, and other non-numeric characters except decimal point and minus
            cleaned = re.sub(r'[^\d.-]', '', str(value))
            if not cleaned:
                return 0.0
            return float(cleaned)
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse numeric value '{value}': {e}")
            return 0.0

    def parse_stock_table(self, table_html) -> List[Dict[str, Any]]:
        """Parse NEPSE stock data table"""
        try:
            stocks = []
            rows = table_html.find_all('tr')
            
            if not rows or len(rows) < 2:
                return []
            
            # Extract headers
            headers = []
            header_row = rows[0]
            for th in header_row.find_all('th'):
                header_text = th.get_text(strip=True)
                headers.append(self.normalize_header(header_text))
            
            # Parse data rows
            for row in rows[1:]:
                stock_data = self.parse_stock_row(row, headers)
                if stock_data:
                    stocks.append(stock_data)
            
            return stocks
            
        except Exception as e:
            logger.error(f"Error parsing stock table: {e}")
            return []

    def parse_stock_row(self, row, headers: List[str]) -> Optional[Dict[str, Any]]:
        """Parse individual stock row"""
        try:
            cells = row.find_all('td')
            if len(cells) < len(headers):
                return None
            
            stock_data = {}
            for i, cell in enumerate(cells):
                if i >= len(headers):
                    break
                    
                header = headers[i]
                cell_text = cell.get_text(strip=True)
                
                # Parse based on header type
                if header in ['open_price', 'high_price', 'low_price', 'close_price', 'change', 'change_percent']:
                    stock_data[header] = self.clean_numeric_value(cell_text)
                elif header == 'volume':
                    stock_data[header] = int(self.clean_numeric_value(cell_text))
                elif header in ['symbol', 'company_name']:
                    stock_data[header] = cell_text
                else:
                    stock_data[header] = cell_text
            
            # Validate required fields
            if not stock_data.get('symbol') or not stock_data.get('company_name'):
                return None
                
            return stock_data
            
        except Exception as e:
            logger.warning(f"Error parsing stock row: {e}")
            return None

    def normalize_header(self, header: str) -> str:
        """Normalize table headers to consistent format"""
        header_lower = header.lower()
        
        header_mapping = {
            'symbol': 'symbol',
            'company': 'company_name',
            'open': 'open_price',
            'high': 'high_price', 
            'low': 'low_price',
            'close': 'close_price',
            'volume': 'volume',
            'change': 'change',
            '% change': 'change_percent',
            'traded shares': 'volume',
            'traded amount': 'traded_amount'
        }
        
        for key, value in header_mapping.items():
            if key in header_lower:
                return value
        
        # Fallback: convert to snake_case
        return header_lower.replace(' ', '_')

    def calculate_market_summary(self, stocks: List[Dict]) -> Dict[str, Any]:
        """Calculate market summary from stock data"""
        try:
            if not stocks:
                return self.get_empty_summary()
            
            advances = len([s for s in stocks if s.get('change', 0) > 0])
            declines = len([s for s in stocks if s.get('change', 0) < 0])
            unchanged = len([s for s in stocks if s.get('change', 0) == 0])
            
            total_turnover = sum(s.get('close_price', 0) * s.get('volume', 0) for s in stocks)
            total_volume = sum(s.get('volume', 0) for s in stocks)
            
            # Calculate average values for mock indices
            if stocks:
                avg_price = sum(s.get('close_price', 0) for s in stocks) / len(stocks)
                nepse_index = avg_price * 1.5  # Mock calculation
                sensitive_index = avg_price * 0.8  # Mock calculation
                float_index = avg_price * 0.6  # Mock calculation
            else:
                nepse_index = sensitive_index = float_index = 0.0
            
            return {
                'nepse_index': round(nepse_index, 2),
                'sensitive_index': round(sensitive_index, 2),
                'float_index': round(float_index, 2),
                'total_turnover': round(total_turnover, 2),
                'total_volume': total_volume,
                'total_trades': len(stocks),
                'advance_decline': {
                    'advances': advances,
                    'declines': declines,
                    'unchanged': unchanged
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating market summary: {e}")
            return self.get_empty_summary()

    def get_empty_summary(self) -> Dict[str, Any]:
        """Return empty market summary"""
        return {
            'nepse_index': 0.0,
            'sensitive_index': 0.0,
            'float_index': 0.0,
            'total_turnover': 0.0,
            'total_volume': 0,
            'total_trades': 0,
            'advance_decline': {
                'advances': 0,
                'declines': 0,
                'unchanged': 0
            }
        }

    def filter_top_gainers(self, stocks: List[Dict], limit: int = 10) -> List[Dict]:
        """Filter top gaining stocks"""
        try:
            gainers = [s for s in stocks if s.get('change_percent', 0) > 0]
            return sorted(gainers, key=lambda x: x.get('change_percent', 0), reverse=True)[:limit]
        except Exception as e:
            logger.error(f"Error filtering top gainers: {e}")
            return []

    def filter_top_losers(self, stocks: List[Dict], limit: int = 10) -> List[Dict]:
        """Filter top losing stocks"""
        try:
            losers = [s for s in stocks if s.get('change_percent', 0) < 0]
            return sorted(losers, key=lambda x: x.get('change_percent', 0))[:limit]
        except Exception as e:
            logger.error(f"Error filtering top losers: {e}")
            return []

    def find_stock_by_symbol(self, stocks: List[Dict], symbol: str) -> Optional[Dict]:
        """Find stock by symbol (case-insensitive)"""
        try:
            symbol_upper = symbol.upper()
            for stock in stocks:
                if stock.get('symbol', '').upper() == symbol_upper:
                    return stock
            return None
        except Exception as e:
            logger.error(f"Error finding stock by symbol: {e}")
            return None

# Global parser instance
data_parser = DataParser()