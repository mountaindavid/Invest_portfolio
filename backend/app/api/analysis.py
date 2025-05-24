"""
Analysis API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..models.asset import Asset
from ..services.yahoo_finance import YahooFinanceService
from ..extensions import db

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/<int:portfolio_id>/performance', methods=['GET'])
@jwt_required()
def get_portfolio_performance(portfolio_id):
    """Portfolio performance analysis"""
    #NOT READY
    #from ..services.ai_analysis import *
    # current_user_id = get_jwt_identity()
    performance_data = None

    if not performance_data:
        return jsonify({'error': 'Portfolio not found or no data'}), 404

    return jsonify(performance_data), 200


@analysis_bp.route('/<int:portfolio_id>/allocation', methods=['GET'])
@jwt_required()
def get_portfolio_allocation(portfolio_id):
    #NOT READY
    allocation_data = None

    if not allocation_data:
        return jsonify({'error': 'Portfolio not found or no data'}), 404

    return jsonify(allocation_data), 200