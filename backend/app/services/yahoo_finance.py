import os
import requests
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from ..extensions import cache, db
from ..models.asset import Asset, AssetPrice, AssetMetric
#from ..models.dividend import Dividend

"""
Service for working with Yahoo Finance API
"""
import os
import requests
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from ..extensions import cache, db
from ..models.asset import Asset, AssetPrice, AssetMetric
from ..models.dividend import Dividend


class YahooFinanceService:
    """Service for interacting with Yahoo Finance API"""

    @staticmethod
    @cache.memoize(timeout=300)  # Cache for 5 minutes
    def get_current_price(ticker):
        """
        Get the current price of an asset
        """
        try:
            ticker_data = yf.Ticker(ticker)
            # Get the latest data
            last_quote = ticker_data.history(period="1d")
            if not last_quote.empty:
                return float(last_quote['Close'].iloc[-1])
            return None
        except Exception as e:
            print(f"Error fetching price for {ticker}: {e}")
            return None

    @staticmethod
    @cache.memoize(timeout=3600)  # Cache for 1 hour
    def get_stock_info(ticker):
        """
        Get information about an asset
        """
        try:
            ticker_data = yf.Ticker(ticker)
            info = ticker_data.info

            # Basic information
            result = {
                'ticker': ticker,
                'name': info.get('longName', info.get('shortName', ticker)),
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', '')
            }

            # Determine asset type
            if 'quoteType' in info:
                if info['quoteType'] == 'EQUITY':
                    result['asset_type'] = 'stock'
                elif info['quoteType'] == 'ETF':
                    result['asset_type'] = 'etf'
                elif info['quoteType'] == 'BOND':
                    result['asset_type'] = 'bond'
                else:
                    result['asset_type'] = 'other'
            else:
                result['asset_type'] = 'stock'  # Default

            return result
        except Exception as e:
            print(f"Error fetching info for {ticker}: {e}")
            return None

    @staticmethod
    def update_asset_historical_data(ticker, period='1y'):
        """
        Update historical data for an asset
        """
        try:
            asset = Asset.query.filter_by(ticker=ticker).first()
            if not asset:
                info = YahooFinanceService.get_stock_info(ticker)
                if info:
                    asset = Asset(
                        ticker=ticker,
                        name=info['name'],
                        asset_type=info['asset_type'],
                        currency=info['currency'],
                        exchange=info['exchange'],
                        sector=info['sector'],
                        industry=info['industry']
                    )
                    db.session.add(asset)
                    db.session.commit()

            if not asset:
                return False

            # Get historical data
            ticker_data = yf.Ticker(ticker)
            hist_data = ticker_data.history(period=period)

            # Delete old data
            AssetPrice.query.filter_by(asset_id=asset.id).delete()

            # Add new data
            for date, row in hist_data.iterrows():
                price = AssetPrice(
                    asset_id=asset.id,
                    date=date.date(),
                    open=float(row['Open']) if 'Open' in row and pd.notnull(row['Open']) else None,
                    high=float(row['High']) if 'High' in row and pd.notnull(row['High']) else None,
                    low=float(row['Low']) if 'Low' in row and pd.notnull(row['Low']) else None,
                    close=float(row['Close']) if 'Close' in row and pd.notnull(row['Close']) else None,
                    volume=int(row['Volume']) if 'Volume' in row and pd.notnull(row['Volume']) else None
                )
                db.session.add(price)

            # Update metrics
            YahooFinanceService.update_asset_metrics(asset)

            # Update dividends
            YahooFinanceService.update_dividends(asset)

            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error updating data for {ticker}: {e}")
            return False

    @staticmethod
    def update_asset_metrics(asset):
        """
        Update financial metrics of an asset
        """
        try:
            ticker_data = yf.Ticker(asset.ticker)
            info = ticker_data.info

            # Delete old metrics
            AssetMetric.query.filter_by(asset_id=asset.id).delete()

            # Create new metrics record
            metrics = AssetMetric(
                asset_id=asset.id,
                date=datetime.now().date(),
                pe_ratio=info.get('trailingPE'),
                pb_ratio=info.get('priceToBook'),
                dividend_yield=info.get('dividendYield'),
                market_cap=info.get('marketCap'),
                eps=info.get('trailingEps'),
                revenue=info.get('totalRevenue'),
                profit_margin=info.get('profitMargins'),
                debt_to_equity=info.get('debtToEquity')
            )
            db.session.add(metrics)
            return True
        except Exception as e:
            print(f"Error updating metrics for {asset.ticker}: {e}")
            return False

    @staticmethod
    def update_dividends(asset):
        """
        Update dividend information
        """
        try:
            ticker_data = yf.Ticker(asset.ticker)

            # Get dividend data
            dividends = ticker_data.dividends

            # Delete old dividend records
            Dividend.query.filter_by(asset_id=asset.id).delete()

            # Add new dividend records
            for date, amount in dividends.items():
                div = Dividend(
                    asset_id=asset.id,
                    ex_date=date.date(),
                    payment_date=None,  # For simplicity, not filling payment date
                    amount=float(amount)
                )
                db.session.add(div)

            return True
        except Exception as e:
            print(f"Error updating dividends for {asset.ticker}: {e}")
            return False

    @staticmethod
    def search_tickers(query):
        """
        Search for stock tickers by query
        """
        try:
            # Use Yahoo Finance API for search
            url = f"https://query2.finance.yahoo.com/v1/finance/search"
            params = {
                'q': query,
                'quotesCount': 10,
                'newsCount': 0
            }

            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if 'quotes' in data:
                    return [
                        {
                            'ticker': item.get('symbol'),
                            'name': item.get('longname', item.get('shortname', '')),
                            'exchange': item.get('exchange', ''),
                            'type': item.get('quoteType', '')
                        }
                        for item in data['quotes']
                    ]
            return []
        except Exception as e:
            print(f"Error searching tickers: {e}")
            return []