"""
Transaction model
"""
from datetime import datetime
from ..extensions import db


class Transaction(db.Model):
    """Transaction model (buy/sell)"""
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    transaction_type = db.Column(db.Enum('buy', 'sell', name='transaction_type'), nullable=False)
    quantity = db.Column(db.Numeric(15, 6), nullable=False)
    price = db.Column(db.Numeric(15, 6), nullable=False)
    fee = db.Column(db.Numeric(15, 6), default=0)
    transaction_date = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def calculate_total(self):
        """Total transaction amount"""
        return float(self.price * self.quantity + self.fee)

    def to_dict(self, include_asset=False):
        """Convert to dict for API"""
        result = {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'asset_id': self.asset_id,
            'transaction_type': self.transaction_type,
            'quantity': float(self.quantity),
            'price': float(self.price),
            'fee': float(self.fee),
            'total': self.calculate_total(),
            'transaction_date': self.transaction_date.isoformat(),
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }

        if include_asset:
            result['asset'] = {
                'ticker': self.asset.ticker,
                'name': self.asset.name,
                'type': self.asset.asset_type
            }

        return result

    def __repr__(self):
        return f'<Transaction {self.transaction_type} {self.asset_id} at {self.transaction_date}>'