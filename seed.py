from app import app
from models import db, User

def create_db():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Create an admin user
        admin = User(
            username='aggreyrc',
            email='admin@example.com',
            password='admin123'
            )
        
        admin.set_password(admin.password)
        try:
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully.")
        except IntegrityError:
            db.session.rollback()
            print("Admin user already exists.")
        print("Database created and admin user added.")
        
if __name__ == '__main__':
    create_db()
    print("Database setup complete.")