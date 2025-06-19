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
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(64), nullable=True)
    
        # Relationships
    orders = db.relationship('Order', back_populates='user', cascade='all, delete-orphan')
    carts = db.relationship('Cart', back_populates='user', cascade='all, delete-orphan')

    # Serialization rules
    serialize_rules = ('-password', '-created_at', '-is_admin', '-orders.user', '-carts.user')

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def generate_reset_token(self):
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        return token
    
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    # Generate a verification token
    def generate_verification_token(self):
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        self.verification_token = token
        try:
            db.session.add(self)
            db.session.commit()
            print(f"Verification token generated for user {self.username}.")
        except IntegrityError:
            db.session.rollback()
            print(f"Error generating verification token for user {self.username}.")
            return None
        return token
    
    # Validate email format
    @staticmethod
    def is_valid_email(email):
        if '@' in email and '.' in email.split('@')[-1]:
            return True
        return False
    
    # Validate username and password and send verification email
    def validate_and_send_verification(self):
        if not self.is_valid_email(self.email):
            raise ValueError("Invalid email format.")
        
        if len(self.username) < 3 or len(self.password) < 6:
            raise ValueError("Username must be at least 3 characters and password at least 6 characters long.")
        
        # Generate verification token
        token = self.generate_verification_token()
        if not token:
            raise ValueError("Failed to generate verification token.")
        send_verification_email(self.email, token)
        
                # Verify token and mark user as verified
    def verify_email(self, token):
            if self.verification_token == token:
                self.is_verified = True
                self.verification_token = None
                db.session.commit()
                return True
            return False
        
        # Compose and send verification email
def send_verification_email(recipient_email, code):

        try:
            msg = Message(
                subject="Your Verification Code",
                sender=os.getenv('MAIL_USERNAME'),
                recipients=[recipient_email],
                body=f"Your verification code is: {code}"
            )
            print(f"Sending verification code {code} to {recipient_email}")
            mail.send(msg)
        except Exception as e:
            print(f"Error sending email: {e}")

            

    

    
    
    
# Product model
class Product(db.Model, SerializerMixin):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    amount_in_stock = db.Column(db.Integer, nullable=False, default=0)
    stock_status = db.Column(db.String(20), nullable=False, default='in_stock')  # in_stock, out_of_stock, low_stock
    
        # Relationships
    orders = db.relationship('Order', back_populates='product', cascade='all, delete-orphan')
    carts = db.relationship('Cart', back_populates='product', cascade='all, delete-orphan')

    # Serialization rules
    serialize_rules = ('-created_at', '-orders.product', '-carts.product')

    def __repr__(self):
        return f'<Product {self.name}>'
# Order model
class Order(db.Model, SerializerMixin):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='orders')
    product = db.relationship('Product', back_populates='orders')
    payment = db.relationship('Payment', back_populates='order', uselist=False, cascade='all, delete-orphan')

    # Serialization rules
    serialize_rules = ('-created_at', '-user.orders', '-product.orders', '-payment.order')
    def __repr__(self):
        return f'<Order {self.id} by User {self.user_id}>'
# Cart model
class Cart(db.Model, SerializerMixin):
    __tablename__ = 'carts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='carts')
    product = db.relationship('Product', back_populates='carts')

    # Serialization rules
    serialize_rules = ('-created_at', '-user.carts', '-product.carts')

    def __repr__(self):
        return f'<Cart {self.id} for User {self.user_id}>'
    
# Payment model
class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # e.g., 'stripe', 'paypal'
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, completed, failed
    transaction_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

       # Relationships
    order = db.relationship('Order', back_populates='payment')

    # Serialization rules
    serialize_rules = ('-created_at', '-order.payment')

    def __repr__(self):
        return f'<Payment {self.id} for Order {self.order_id}>'