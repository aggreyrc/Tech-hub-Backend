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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)