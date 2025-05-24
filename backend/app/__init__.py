from flask import Flask
from flask_cors import CORS
from .config import config
from .extensions import db, jwt, migrate, cache

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    #Init extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    CORS(app)

    #Register API blueprints
    from .api import auth, portfolio, assets, analysis
    app.register_blueprint(auth.auth_bp, url_prefix='/api/auth')
    app.register_blueprint(portfolio.portfolio_bp, url_prefix='/api/portfolios')
    app.register_blueprint(assets.asset_bp, url_prefix='/api/assets')
    app.register_blueprint(analysis.analysis_bp, url_prefix='/api/analysis')

    @app.route('/')
    def index():
        return {'message': 'Backend is running!'}

    # Error handler
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500

    return app