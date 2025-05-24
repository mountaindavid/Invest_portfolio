"""
Assets API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..models.asset import Asset
from ..services.yahoo_finance import YahooFinanceService
from ..extensions import db

asset_bp = Blueprint('asset', __name__)

@asset_bp.route('/assets', methods=['GET'])
@jwt_required()
def get_assets():
    """List of all assets"""
    assets = Asset.query.all()
    return jsonify({'assets': [asset.to_dict() for asset in assets]}), 200

@asset_bp.route('/<string:ticker>', methods=['GET'])
@jwt_required()
def get_asset(ticker):
    """Info by ticker"""
    asset = Asset.query.filter_by(ticker=ticker.upper()).first()
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404
    return jsonify(asset.to_dict(include_history=True)), 200


@asset_bp.route('/sync/<string:ticker>', methods=['POST'])
@jwt_required()
def sync_asset(ticker):
    """Refresh or add asset from YahooFinance"""
    ticker = ticker.upper()
    asset_info = YahooFinanceService.get_stock_info(ticker)
    if not asset_info:
        return jsonify({'error': 'Invalid ticker symbol'}), 400

    asset = Asset.query.filter_by(ticker=ticker).first()
    if not asset:
        asset = Asset(**asset_info)
        db.session.add(asset)
    else:
        for key, value in asset_info.items():
            setattr(asset, key, value)

    db.session.commit()
    YahooFinanceService.update_asset_historical_data(ticker)

    return jsonify({'message': 'Asset synced successfully', 'asset': asset.to_dict()}), 200
