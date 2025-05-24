"""
Asset model
"""
from datetime import datetime
from sqlalchemy import func
from ..extensions import db, cache

class Asset(db.Model):
    __tablename__ = "asset"

    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    asset_type = db.Column(db.Enum('stock', 'bond', 'etf', 'other', name='asset_type'), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    exchange = db.Column(db.String(50))
    sector = db.Column(db.String(100))
    industry = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    prices = db.relationship('AssetPrice', backref='asset', lazy='dynamic', cascade='all, delete-orphan')
    metrics = db.relationship('AssetMetric', backref='asset', lazy='dynamic', cascade='all, delete-orphan')
    dividends = db.relationship('Dividend', backref='asset', lazy='dynamic', cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='asset', lazy='dynamic')

    def get_current_price(self):
        from ..services.yahoo_finance import YahooFinanceService
        #check cache or db
        latest_price = AssetPrice.query.filer_by(asset_id=self.id).order_by(AssetPrice.date.desc()).first()

        if latest_price and latest_price.date == datetime.now().date():
            return latest_price.close

        current_price = YahooFinanceService.get_current_price(self.ticker)
        if current_price:
            return current_price

        if latest_price:
            return latest_price.close

        return None

    def get_price_history(self, period='1m'):
        """Get price history"""
        # From db
        prices = AssetPrice.query.filter_by(asset_id=self.id).order_by(AssetPrice.date).all()
        return [
            {
                'date': price.date.isoformat(),
                'open': price.open,
                'high': price.high,
                'low': price.low,
                'close': price.close,
                'volume': price.volume
            }
            for price in prices
        ]

    def get_latest_metrics(self):
        """Get latest metrics"""
        metrics = AssetMetric.query.filter_by(asset_id=self.id).order_by(AssetMetric.date.desc()).first()
        if metrics:
            return {
                'date': metrics.date.isoformat(),
                'pe_ratio': metrics.pe_ratio,
                'pb_ratio': metrics.pb_ratio,
                'dividend_yield': metrics.dividend_yield,
                'market_cap': metrics.market_cap,
                'eps': metrics.eps,
                'revenue': metrics.revenue,
                'profit_margin': metrics.profit_margin,
                'debt_to_equity': metrics.debt_to_equity
            }
        return None

    def get_dividends(self):
        """Get dividends"""
        dividends = Dividend.query.filter_by(asset_id=self.id).order_by(Dividend.ex_date).all()
        return [
            {
                'ex_date': div.ex_date.isoformat(),
                'payment_date': div.payment_date.isoformat() if div.payment_date else None,
                'amount': div.amount
            }
            for div in dividends
        ]

    def to_dict(self, include_details=False):
        """Convert to dict for API"""
        result = {
            'id': self.id,
            'ticker': self.ticker,
            'name': self.name,
            'asset_type': self.asset_type,
            'currency': self.currency,
            'exchange': self.exchange,
            'sector': self.sector,
            'industry': self.industry,
            'current_price': self.get_current_price()
        }

        if include_details:
            result.update({
                'metrics': self.get_latest_metrics(),
                'dividends': self.get_dividends()
            })

        return result

    def __repr__(self):
        return f'<Asset {self.ticker}>'


class AssetPrice(db.Model):
    """Asset price Model"""
    __tablename__ = 'asset_prices'

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    open = db.Column(db.Numeric(15, 6))
    high = db.Column(db.Numeric(15, 6))
    low = db.Column(db.Numeric(15, 6))
    close = db.Column(db.Numeric(15, 6), nullable=False)
    volume = db.Column(db.BigInteger)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('asset_id', 'date', name='_asset_date_uc'),)

    def __repr__(self):
        return f'<AssetPrice {self.asset_id} on {self.date}>'


class AssetMetric(db.Model):
    """Asset financial metrics Model"""
    __tablename__ = 'asset_metrics'

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    pe_ratio = db.Column(db.Numeric(15, 6))
    pb_ratio = db.Column(db.Numeric(15, 6))
    dividend_yield = db.Column(db.Numeric(10, 6))
    market_cap = db.Column(db.Numeric(20, 2))
    eps = db.Column(db.Numeric(15, 6))
    revenue = db.Column(db.Numeric(20, 2))
    profit_margin = db.Column(db.Numeric(10, 6))
    debt_to_equity = db.Column(db.Numeric(15, 6))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('asset_id', 'date', name='_asset_metrics_date_uc'),)

    def __repr__(self):
        return f'<AssetMetric {self.asset_id} on {self.date}>'


class Dividend(db.Model):
    """Dividend Model"""
    __tablename__ = 'dividends'

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    ex_date = db.Column(db.Date, nullable=False)
    payment_date = db.Column(db.Date)
    amount = db.Column(db.Numeric(15, 6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    asset = db.relationship('Asset', backref=db.backref('dividends', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Dividend {self.asset_id} on {self.ex_date}>'