"""Flask extensions"""

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_caching import Cache

#Extensions initialization
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
cache = Cache(config={
    "CACHE_TYPE": "simple",
    "CACHE_REDIS_URL": "redis://redis:6379/0",
    "CACHE_DEFAULT_TIMEOUT": 300
})
