from app import app
from models import db, User, Product
from sqlalchemy.exc import IntegrityError

def create_db():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Create users
        users = [
            User(username='aggreyrc', email='admin@example.com', password='admin123', is_admin=True, is_verified=True),
            User(username='johndoe', email='john@example.com', password='johnpass', is_admin=False, is_verified=False),
            User(username='janedoe', email='jane@example.com', password='janepass', is_admin=False, is_verified=False),
        ]
        for user in users:
            user.set_password(user.password)
            try:
                db.session.add(user)
                db.session.commit()
                print(f"User {user.username} created successfully.")
            except IntegrityError:
                db.session.rollback()
                print(f"User {user.username} already exists.")

        # Create products (laptops and phones)
        products = [
            Product(
                name='Dell XPS 13',
                description='13-inch laptop with InfinityEdge display',
                price=1200.00,
                image_path='uploads/laptop1.jpg',
                amount_in_stock=10,
                stock_status='in_stock'
            ),
            Product(
                name='MacBook Pro 16',
                description='Apple 16-inch laptop with M1 chip',
                price=2500.00,
                image_path='uploads/laptop2.jpg',
                amount_in_stock=5,
                stock_status='in_stock'
            ),
            Product(
                name='HP Spectre x360',
                description='Convertible 2-in-1 laptop',
                price=1400.00,
                image_path='uploads/laptop3.jpg',
                amount_in_stock=3,
                stock_status='low_stock'
            ),
            Product(
                name='iPhone 14',
                description='Apple smartphone with A15 Bionic chip',
                price=999.00,
                image_path='uploads/phone1.jpg',
                amount_in_stock=0,
                stock_status='out_of_stock'
            ),
            Product(
                name='Samsung Galaxy S22',
                description='Samsung flagship smartphone',
                price=899.00,
                image_path='uploads/phone2.jpg',
                amount_in_stock=8,
                stock_status='in_stock'
            ),
            Product(
                name='Google Pixel 7',
                description='Google smartphone with pure Android',
                price=799.00,
                image_path='uploads/phone3.jpg',
                amount_in_stock=2,
                stock_status='low_stock'
            ),
        ]
        for product in products:
            try:
                db.session.add(product)
                db.session.commit()
                print(f"Product {product.name} created successfully.")
            except IntegrityError:
                db.session.rollback()
                print(f"Product {product.name} already exists.")
        print("Database created and sample users/products added.")
        
        
if __name__ == '__main__':
    create_db()
    print("Database setup complete.")