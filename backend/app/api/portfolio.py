"""
Portfolio API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.portfolio import Portfolio
from ..models.transaction import Transaction
from ..models.asset import Asset
from ..services.yahoo_finance import YahooFinanceService
from ..extensions import db

portfolio_bp = Blueprint('portfolio', __name__, url_prefix='/portfolio')


@portfolio_bp.route('/', methods=['GET'])
@jwt_required()
def get_portfolios():
    """Current user's portfolios"""
    current_user_id = get_jwt_identity()
    portfolios = Portfolio.query.filter_by(user_id=current_user_id).all()

    return jsonify({
        'portfolios': [portfolio.to_dict() for portfolio in portfolios]
    }), 200


@portfolio_bp.route('/<int:portfolio_id>', methods=['GET'])
@jwt_required()
def get_portfolio(portfolio_id):
    """Actual portfolio"""
    current_user_id = get_jwt_identity()
    portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user_id).first()

    if not portfolio:
        return jsonify({'error': 'Portfolio not found'}), 404

    return jsonify(portfolio.to_dict(include_assets=True)), 200


@portfolio_bp.route('/', methods=['POST'])
@jwt_required()
def create_portfolio():
    """Create new portfolio"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    # check all necessary fields
    if 'name' not in data:
        return jsonify({'error': 'Portfolio name is required'}), 400

    # create new
    portfolio = Portfolio(
        user_id=current_user_id,
        name=data['name'],
        description=data.get('description', '')
    )

    db.session.add(portfolio)
    db.session.commit()

    return jsonify({
        'message': 'Portfolio created successfully',
        'portfolio': portfolio.to_dict()
    }), 201


@portfolio_bp.route('/<int:portfolio_id>', methods=['PUT'])
@jwt_required()
def update_portfolio(portfolio_id):
    """Update portfolio"""
    current_user_id = get_jwt_identity()
    portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user_id).first()

    if not portfolio:
        return jsonify({'error': 'Portfolio not found'}), 404

    data = request.get_json()

    if 'name' in data:
        portfolio.name = data['name']

    if 'description' in data:
        portfolio.description = data['description']

    db.session.commit()

    return jsonify({
        'message': 'Portfolio updated successfully',
        'portfolio': portfolio.to_dict()
    }), 200


@portfolio_bp.route('/<int:portfolio_id>', methods=['DELETE'])
@jwt_required()
def delete_portfolio(portfolio_id):
    """Delete portfolio"""
    current_user_id = get_jwt_identity()
    portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user_id).first()

    if not portfolio:
        return jsonify({'error': 'Portfolio not found'}), 404

    db.session.delete(portfolio)
    db.session.commit()

    return jsonify({
        'message': 'Portfolio deleted successfully'
    }), 200


@portfolio_bp.route('/<int:portfolio_id>/transactions', methods=['GET'])
@jwt_required()
def get_portfolio_transactions(portfolio_id):
    """Portfolio transactions"""
    current_user_id = get_jwt_identity()
    portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user_id).first()

    if not portfolio:
        return jsonify({'error': 'Portfolio not found'}), 404

    transactions = Transaction.query.filter_by(portfolio_id=portfolio_id).order_by(
        Transaction.transaction_date.desc()).all()

    return jsonify({
        'transactions': [transaction.to_dict(include_asset=True) for transaction in transactions]
    }), 200


@portfolio_bp.route('/<int:portfolio_id>/transactions', methods=['POST'])
@jwt_required()
def add_transaction(portfolio_id):
    """Add transaction"""
    current_user_id = get_jwt_identity()
    portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user_id).first()

    if not portfolio:
        return jsonify({'error': 'Portfolio not found'}), 404

    data = request.get_json()

    # Check necessary fields
    required_fields = ['ticker', 'transaction_type', 'quantity', 'price', 'transaction_date']
    if not all(key in data for key in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    # Get or create an asset
    asset = Asset.query.filter_by(ticker=data['ticker']).first()
    if not asset:
        # Get asset info
        asset_info = YahooFinanceService.get_stock_info(data['ticker'])
        if not asset_info:
            return jsonify({'error': 'Invalid ticker symbol'}), 400

        # Create new asset
        asset = Asset(
            ticker=asset_info['ticker'],
            name=asset_info['name'],
            asset_type=asset_info['asset_type'],
            currency=asset_info['currency'],
            exchange=asset_info['exchange'],
            sector=asset_info['sector'],
            industry=asset_info['industry']
        )
        db.session.add(asset)
        db.session.flush()  # Для получения ID актива

        # Update asset historical data
        YahooFinanceService.update_asset_historical_data(data['ticker'])