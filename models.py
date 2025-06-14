import random
import string
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from flask_mail import Mail, Message
from sqlalchemy_serializer import SerializerMixin
from dotenv import load_dotenv
load_dotenv()

import os

db =SQLAlchemy()
bcrypt=Bcrypt()
mail = Mail()

# User model
class User(db.Model, SerializerMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def generate_reset_token(self):
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        return token
    
    def __repr__(self):
        return f'<User {self.username}>'