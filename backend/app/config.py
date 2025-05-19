import os
from datetime import timedelta

from CLAUDE.config_file import Config


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ['SECRET_KEY']
    JWT_SECRET_KEY = os.environ['JWT_SECRET_KEY']
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    #Mysql config
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    #YAHOO Finance API
    YAHOO_FINANCE_API_KEY = os.environ['YAHOO_FINANCE_API_KEY']

    #REDIS
    REDIS_URL = os.environ['REDIS_URL']

    @staticmethod
    def init_app(app):
        """app initialization."""
        pass

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ['DEV_DATABASE_URL']

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ['TEST_DATABASE_URL']

class ProductionConfig(Config):
    """Production configuration."""
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']

    @classmethod
    def init(cls, app):
        Config.init_app(app)

        #Logging for prod
        import logging
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler('logs/portfolio.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Portfolio Monitor startup')

#Config dict
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
    }