"""
Portfolio model
"""
from datetime import datetime
from sqlalchemy import func
from ..extensions import db

class Portfolio(db.Model):
    __tablename__ = 'portfolio'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    #relations
    transactions = db.relationship('Transaction', backref='portfolio', lazy='dynamic', cascade='all, delete-orphan')
    analyses = db.relationship('PortfolioAnalysis', backref='portfolio', lazy='dynamic', cascade='all, delete-orphan')

    def calculate_total_value(self):
        """Total value of portfolio"""
        from .asset import Asset
        from .transaction import Transaction

        total_value = 0

        asset_holdings = db.session.query(
            Transaction.asset_id,
            func.sum(Transaction.quantity).label('total_quantity')
        ).filter(
            Transaction.portfolio_id == self.id
        ).group_by(Transaction.asset_id).all()


        for asset_id, quantity in asset_holdings:
            asset = Asset.query.get(asset_id)
            if asset and quantity > 0:
                current_price = asset.get_current_price()
                total_value += current_price * quantity

        return total_value


    def calculate_total_profit(self):
        """Total value of portfolio"""
        from .transaction import Transaction

        buy_transactions = Transaction.query.filter_by(portfolio_id=self.id, transaction_type='buy').all()
        sell_transactions = Transaction.query.filter_by(portfolio_id=self.id, transaction_type='sell').all()

        total_buy_cost = sum(t.price * t.quantity for t in buy_transactions)
        total_sell_value = sum(t.price * t.quantity for t in sell_transactions)

        current_value = self.calculate_total_value()

        total_profit = (current_value + total_sell_value) - total_buy_cost

        return total_profit

    def to_dict(self, include_assets=False):
        """Convert to dict for API"""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'total_value': self.calculate_total_value(),
            'total_profit': self.calculate_total_profit()
        }

        if include_assets:
            result['assets'] = self.get_assets_summary()

        return result

    def get_assets_summary(self):
        from .asset import Asset
        from .transaction import Transaction

        # Grouped data
        asset_holdings = db.session.query(
            Transaction.asset_id,
            func.sum(Transaction.quantity).label('total_quantity')
        ).filter(
            Transaction.portfolio_id == self.id
        ).group_by(Transaction.asset_id).all()

        assets_summary = []

        for asset_id, quantity in asset_holdings:
            if quantity <= 0:  # Skip sold assets
                continue

            asset = Asset.query.get(asset_id)

            # Average buy price
            buy_transactions = Transaction.query.filter_by(
                portfolio_id=self.id, asset_id=asset_id, transaction_type='buy').all()
            total_cost = sum(t.price * t.quantity for t in buy_transactions)
            total_bought = sum(t.quantity for t in buy_transactions)
            avg_buy_price = total_cost / total_bought if total_bought > 0 else 0

            current_price = asset.get_current_price()
            profit_percent = ((current_price / avg_buy_price) - 1) * 100 if avg_buy_price > 0 else 0

            assets_summary.append({
                'asset_id': asset_id,
                'ticker': asset.ticker,
                'name': asset.name,
                'quantity': quantity,
                'avg_buy_price': avg_buy_price,
                'current_price': current_price,
                'total_value': current_price * quantity,
                'profit_percent': profit_percent
            })

        return assets_summary

    def __repr__(self):
        return f'<Portfolio {self.name} of User {self.user_id}>'
