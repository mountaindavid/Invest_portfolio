"""
User model
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    #relations
    portfolios = db.relationship('Portfolio', backref='user', lazy="dynamic", cascade='all, delete-orphan')

    @property
    def password(self):
        """password access restricted"""
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        """password setter"""
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """verify password against password"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """convert to dict for API"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<User {self.username}>'