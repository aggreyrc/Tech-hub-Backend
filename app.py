# from dotenv import load_dotenv
# load_dotenv()

from datetime import datetime

from flask import request, make_response, session, Flask,jsonify
from flask_migrate import Migrate
from flask_restful import Resource,Api
from flask_cors import CORS


from models import db, User, bcrypt, mail, Product, Order, Cart
import os

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)

bcrypt.init_app(app)
mail.init_app(app)
CORS(app)
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)