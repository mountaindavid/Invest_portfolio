from flask import Flask, render_template, request
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

    #Register API blueprints
    from .api import auth, portfolio, assets
    app.register_blueprint(auth.auth_bp, url_prefix='/api/auth')
    app.register_blueprint(portfolio.portfolio_bp, url_prefix='/api/portfolios')
    app.register_blueprint(assets.asset_bp, url_prefix='/api/assets')

    @app.route('/')
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/portfolio')
    def portfolio_view():
        return render_template('portfolio.html')

    @app.route('/portfolio/<int:portfolio_id>')
    def portfolio_detail(portfolio_id):
        return render_template('portfolio_detail.html', portfolio_id=portfolio_id)

    @app.route('/assets')
    def assets_view():
        return render_template('assets.html')

    @app.route('/login')
    def login_view():
        return render_template('auth/login.html')

    @app.route('/register')
    def register_view():
        return render_template('auth/register.html')

    # Health check for API consumers
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'message': 'API is running!'}, 200

    # Error handler
    @app.errorhandler(404)
    def not_found(error):
        # API request - returns JSON
        if request.path.startswith('/api/'):
            return {'error': 'Resource not found'}, 404
        # Else - HTML page
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if request.path.startswith('/api/'):
            return {'error': 'Internal server error'}, 500
        return render_template('errors/500.html'), 500

    # Template helpers
    @app.template_global()
    def get_user_portfolios():
        """Helper function for templates"""
        # Ваша логика получения портфолио пользователя
        pass

    return app