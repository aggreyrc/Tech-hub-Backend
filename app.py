# from dotenv import load_dotenv
# load_dotenv()

from datetime import datetime

from flask import request, make_response, session, Flask,jsonify
from flask_migrate import Migrate
from flask_restful import Resource,Api
from flask_cors import CORS
from functools import wraps


from models import db, User, bcrypt, mail, Product, Order, Cart, Payment, send_verification_email
import os
import requests

app = Flask(__name__)

# Paystack secret key from environment variable
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY')
PAYSTACK_BASE_URL = 'https://api.paystack.co'

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

migrate = Migrate(app, db)
db.init_app(app)

bcrypt.init_app(app)
mail.init_app(app)
CORS(app, supports_credentials=True, origins=["http://localhost:8080"])
api = Api(app)

# Home
class Home(Resource):
    def get(self):
        return make_response(jsonify({"message": "Welcome to the Tech-Hub API"}), 200)
    

api.add_resource(Home, '/')

# Get users
class UserList(Resource):
    def get(self):
        users = User.query.all()
        return make_response(jsonify([user.to_dict() for user in users]), 200)
    
api.add_resource(UserList, '/users')

# Image upload endpoint
class ImageUpload(Resource):
    def post(self):
        if 'image' not in request.files or 'product_id' not in request.form:
            return make_response(jsonify({'error': 'Image file and product_id are required.'}), 400)
        image = request.files['image']
        product_id = request.form['product_id']
        if image.filename == '':
            return make_response(jsonify({'error': 'No selected file.'}), 400)
        product = db.session.get(Product, product_id)
        if not product:
            return make_response(jsonify({'error': 'Product not found.'}), 404)
        # Save image
        filename = f"product_{product_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{image.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)
        # Store relative path in DB
        product.image_path = f"uploads/{filename}"
        db.session.commit()
        return make_response(jsonify({'message': 'Image uploaded successfully.', 'image_path': product.image_path}), 201)

api.add_resource(ImageUpload, '/upload-image')

# Create a new user
class UserCreate(Resource):
    def post(self):
        data = request.get_json()
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return make_response(jsonify({'error': 'Username, email, and password are required.'}), 400)
        
        user = User(username=data['username'], email=data['email'])
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return make_response(jsonify(user.to_dict()), 201)
api.add_resource(UserCreate, '/users/create')

# Get a specific user by ID
class UserDetail(Resource):
    def get(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            return make_response(jsonify({'error': 'User not found.'}), 404)
        return make_response(jsonify(user.to_dict()), 200)
api.add_resource(UserDetail, '/users/<int:user_id>')

# Update a user
class UserUpdate(Resource):
    def put(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            return make_response(jsonify({'error': 'User not found.'}), 404)
        
        data = request.get_json()
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'password' in data:
            user.set_password(data['password'])
        
        db.session.commit()
        return make_response(jsonify(user.to_dict()), 200)
api.add_resource(UserUpdate, '/users/<int:user_id>/update')

# Delete a user
class UserDelete(Resource):
    def delete(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            return make_response(jsonify({'error': 'User not found.'}), 404)
        
        db.session.delete(user)
        db.session.commit()
        return make_response(jsonify({'message': 'User deleted successfully.'}), 200)
api.add_resource(UserDelete, '/users/<int:user_id>/delete')


# Get all products
class ProductList(Resource):
    def get(self):
        products = Product.query.all()
        return make_response(jsonify([product.to_dict() for product in products]), 200)
api.add_resource(ProductList, '/products')

# Create a new product
class ProductCreate(Resource):
    def post(self):
        data = request.get_json()
        if not data or not data.get('name') or not data.get('price'):
            return make_response(jsonify({'error': 'Name and price are required.'}), 400)
        
        product = Product(name=data['name'], description=data.get('description'), price=data['price'])
        db.session.add(product)
        db.session.commit()
        
        return make_response(jsonify(product.to_dict()), 201)
api.add_resource(ProductCreate, '/products/create')

# Get a specific product by ID
class ProductDetail(Resource):
    def get(self, product_id):
        product = db.session.get(Product, product_id)
        if not product:
            return make_response(jsonify({'error': 'Product not found.'}), 404)
        return make_response(jsonify(product.to_dict()), 200)
api.add_resource(ProductDetail, '/products/<int:product_id>')

# Update a product
class ProductUpdate(Resource):
    def put(self, product_id):
        product = db.session.get(Product, product_id)
        if not product:
            return make_response(jsonify({'error': 'Product not found.'}), 404)
        
        data = request.get_json()
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'price' in data:
            product.price = data['price']
        
        db.session.commit()
        return make_response(jsonify(product.to_dict()), 200)
api.add_resource(ProductUpdate, '/products/<int:product_id>/update')

# Delete a product
class ProductDelete(Resource):
    def delete(self, product_id):
        product = db.session.get(Product, product_id)
        if not product:
            return make_response(jsonify({'error': 'Product not found.'}), 404)
        
        db.session.delete(product)
        db.session.commit()
        return make_response(jsonify({'message': 'Product deleted successfully.'}), 200)
    
api.add_resource(ProductDelete, '/products/<int:product_id>/delete')

# Get all orders
class OrderList(Resource):
    def get(self):
        orders = Order.query.all()
        return make_response(jsonify([order.to_dict() for order in orders]), 200)
api.add_resource(OrderList, '/orders')


# Create a new order
class OrderCreate(Resource):
    def post(self):
        data = request.get_json()
        # Check for required fields
        if not data:
            return make_response(jsonify({'error': 'Request body must be JSON.'}), 400)
        missing_fields = [field for field in ['user_id', 'product_id', 'quantity'] if field not in data]
        if missing_fields:
            return make_response(jsonify({'error': f"Missing fields: {', '.join(missing_fields)}"}), 400)

        # Validate user_id and product_id are integers
        try:
            user_id = int(data['user_id'])
            product_id = int(data['product_id'])
        except (ValueError, TypeError):
            return make_response(jsonify({'error': 'User ID and Product ID must be integers.'}), 400)

        # Validate quantity is a positive integer
        try:
            quantity = int(data['quantity'])
            if quantity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return make_response(jsonify({'error': 'Quantity must be a positive integer.'}), 400)

        # Check if user exists
        user = db.session.get(User, user_id)
        if not user:
            return make_response(jsonify({'error': 'User not found.'}), 404)

        # Check if product exists
        product = db.session.get(Product, product_id)
        if not product:
            return make_response(jsonify({'error': 'Product not found.'}), 404)

        # Optionally, check if product is in stock, etc.

        order = Order(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(order)
        db.session.commit()

        return make_response(jsonify(order.to_dict()), 201)

api.add_resource(OrderCreate, '/orders/create')

# Get a specific order by ID
class OrderDetail(Resource):
    def get(self, order_id):
        order = db.session.get(Order, order_id)
        if not order:
            return make_response(jsonify({'error': 'Order not found.'}), 404)
        return make_response(jsonify(order.to_dict()), 200)
api.add_resource(OrderDetail, '/orders/<int:order_id>')

# Update an order
class OrderUpdate(Resource):
    def put(self, order_id):
        order = db.session.get(Order, order_id)
        if not order:
            return make_response(jsonify({'error': 'Order not found.'}), 404)
        
        data = request.get_json()
        if 'user_id' in data:
            order.user_id = data['user_id']
        if 'product_id' in data:
            order.product_id = data['product_id']
        if 'quantity' in data:
            order.quantity = data['quantity']
        
        db.session.commit()
        return make_response(jsonify(order.to_dict()), 200)
api.add_resource(OrderUpdate, '/orders/<int:order_id>/update')

# Delete an order  
class OrderDelete(Resource):
    def delete(self, order_id):
        order = db.session.get(Order, order_id)
        if not order:
            return make_response(jsonify({'error': 'Order not found.'}), 404)
        
        db.session.delete(order)
        db.session.commit()
        return make_response(jsonify({'message': 'Order deleted successfully.'}), 200)
api.add_resource(OrderDelete, '/orders/<int:order_id>/delete')

# Get all carts
class CartList(Resource):
    def get(self):
        carts = Cart.query.all()
        return make_response(jsonify([cart.to_dict() for cart in carts]), 200)
api.add_resource(CartList, '/carts')

# Create a new cart
class CartCreate(Resource):
    def post(self):
        data = request.get_json()
        if not data or not data.get('user_id') or not data.get('product_id') or not data.get('quantity'):
            return make_response(jsonify({'error': 'User ID, product ID, and quantity are required.'}), 400)
        
        cart = Cart(user_id=data['user_id'], product_id=data['product_id'], quantity=data['quantity'])
        db.session.add(cart)
        db.session.commit()
        
        return make_response(jsonify(cart.to_dict()), 201)
api.add_resource(CartCreate, '/carts/create')

# Get a specific cart by ID
class CartDetail(Resource):
    def get(self, cart_id):
        cart = db.session.get(Cart, cart_id)
        if not cart:
            return make_response(jsonify({'error': 'Cart not found.'}), 404)
        return make_response(jsonify(cart.to_dict()), 200)
api.add_resource(CartDetail, '/carts/<int:cart_id>')

# Update a cart
class CartUpdate(Resource):
    def put(self, cart_id):
        cart = db.session.get(Cart, cart_id)
        if not cart:
            return make_response(jsonify({'error': 'Cart not found.'}), 404)
        
        data = request.get_json()
        if 'user_id' in data:
            cart.user_id = data['user_id']
        if 'product_id' in data:
            cart.product_id = data['product_id']
        if 'quantity' in data:
            cart.quantity = data['quantity']
        
        db.session.commit()
        return make_response(jsonify(cart.to_dict()), 200)
api.add_resource(CartUpdate, '/carts/<int:cart_id>/update')

# Delete a cart
class CartDelete(Resource):
    def delete(self, cart_id):
        cart = db.session.get(Cart, cart_id)
        if not cart:
            return make_response(jsonify({'error': 'Cart not found.'}), 404)
        
        db.session.delete(cart)
        db.session.commit()
        return make_response(jsonify({'message': 'Cart deleted successfully.'}), 200)
api.add_resource(CartDelete, '/carts/<int:cart_id>/delete')



# --- Authentication & Session Management Utilities ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return make_response(jsonify({'error': 'Authentication required.'}), 401)
        user = db.session.get(User, user_id)
        if not user:
            session.pop('user_id', None)
            return make_response(jsonify({'error': 'Invalid session.'}), 401)
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return make_response(jsonify({'error': 'Authentication required.'}), 401)
        user = db.session.get(User, user_id)
        if not user or not getattr(user, 'is_admin', False):
            return make_response(jsonify({'error': 'Admin privileges required.'}), 403)
        return f(*args, **kwargs)
    return decorated_function

# --- Authentication Endpoints ---

class Login(Resource):
    def post(self):
        data = request.get_json()
        if not data or not data.get('email') or not data.get('password'):
            return make_response(jsonify({'error': 'Email and password are required.'}), 400)
        user = User.query.filter_by(email=data['email']).first()
        if not user or not user.check_password(data['password']):
            return make_response(jsonify({'error': 'Invalid email or password.'}), 401)
        session['user_id'] = user.id
        resp = make_response(jsonify({'message': 'Login successful.', 'user': user.to_dict()}), 200)
        resp.set_cookie('session', session.sid if hasattr(session, 'sid') else '', httponly=True, samesite='Lax')
        return resp

class Logout(Resource):
    @login_required
    def post(self):
        session.pop('user_id', None)
        resp = make_response(jsonify({'message': 'Logout successful.'}), 200)
        resp.delete_cookie('session')
        return resp

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return make_response(jsonify({'authenticated': False}), 200)
        user = db.session.get(User, user_id)
        if not user:
            session.pop('user_id', None)
            return make_response(jsonify({'authenticated': False}), 200)
        return make_response(jsonify({'authenticated': True, 'user': user.to_dict()}), 200)

# Example of a protected route
class ProtectedUserProfile(Resource):
    @login_required
    def get(self):
        user_id = session.get('user_id')
        user = db.session.get(User, user_id)
        return make_response(jsonify({'user': user.to_dict()}), 200)

# Example of an admin-only route
class AdminDashboard(Resource):
    @admin_required
    def get(self):
        return make_response(jsonify({'message': 'Welcome, admin!'}), 200)
    

# Signup endpoint
class Signup(Resource):
    def post(self):
        data = request.get_json()
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return make_response(jsonify({'error': 'Username, email, and password are required.'}), 400)
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return make_response(jsonify({'error': 'User with this email already exists.'}), 400)
        
        
        user = User(username=data['username'], email=data['email'])
        user.set_password(data['password'])
        
        # Generate verification token
        user.generate_verification_token()
        send_verification_email(user.email, user.verification_token)

        db.session.add(user)
        db.session.commit()
        
        session ['user_id'] = user.id
        
        new_user = user.to_dict()
        
        
        return make_response(jsonify({'message': 'User created successfully. Please verify your email.', 'user': new_user}), 201)

# Code verification endpoint
class VerifyEmail(Resource):
    def post(self):
        data = request.get_json()
        if not data or not data.get('token'):
            return make_response(jsonify({'error': 'Verification token is required.'}), 400)
        
        user = User.query.filter_by(verification_token=data['token']).first()
        if not user:
            return make_response(jsonify({'error': 'Invalid verification token.'}), 400)
        
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        
        return make_response(jsonify({'message': 'Email verified successfully.', 'user': user.to_dict()}), 200)
    

# --- Register new endpoints ---
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check-session')
api.add_resource(ProtectedUserProfile, '/profile')
api.add_resource(AdminDashboard, '/admin/dashboard')
api.add_resource(Signup, '/signup')
api.add_resource(VerifyEmail, '/verify-email')


# --- Paystack Payment Integration ---
class PaystackInitialize(Resource):
    def post(self):
        data = request.get_json()
        email = data.get('email')
        amount = data.get('amount')
        if not email or not amount:
            return make_response(jsonify({'error': 'Email and amount are required.'}), 400)
        try:
            amount_kobo = int(float(amount) * 100)  # Paystack expects amount in kobo
        except Exception:
            return make_response(jsonify({'error': 'Invalid amount.'}), 400)
        headers = {
            'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        payload = {
            'email': email,
            'amount': amount_kobo,
        }
        response = requests.post(f'{PAYSTACK_BASE_URL}/transaction/initialize', json=payload, headers=headers)
        resp_json = response.json()
        if not resp_json.get('status'):
            return make_response(jsonify({'error': resp_json.get('message', 'Paystack error')}), 400)
        return make_response(jsonify({'authorization_url': resp_json['data']['authorization_url'], 'reference': resp_json['data']['reference']}), 200)

class PaystackCallback(Resource):
    def get(self):
        reference = request.args.get('reference')
        if not reference:
            return make_response(jsonify({'error': 'Reference is required.'}), 400)
        headers = {
            'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
        }
        response = requests.get(f'{PAYSTACK_BASE_URL}/transaction/verify/{reference}', headers=headers)
        resp_json = response.json()
        if not resp_json.get('status'):
            return make_response(jsonify({'error': resp_json.get('message', 'Verification failed')}), 400)
        # Here you can update your Payment model, mark order as paid, etc.
        return make_response(jsonify({'message': 'Payment verified successfully.', 'data': resp_json['data']}), 200)

api.add_resource(PaystackInitialize, '/paystack/initialize')
api.add_resource(PaystackCallback, '/paystack/callback')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)