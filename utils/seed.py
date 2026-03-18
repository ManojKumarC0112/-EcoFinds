from extensions import db
from models import User, Product, ProductImage
import random

def seed_database():
    if Product.query.count() > 0:
        return # already seeded
        
    # Users
    if User.query.count() == 0:
        users = [
            User(identifier='demo@ecofinds.com', username='Demo User'),
            User(identifier='seller@ecofinds.com', username='EcoSeller Pro'),
            User(identifier='jane@example.com', username='Jane Doe')
        ]
        db.session.add_all(users)
        db.session.commit()
    
    # Products
    sample_products = [
        {
            'title': 'Refurbished MacBook Pro M1',
            'desc': 'Perfect condition. Fully battery health. Giving this a second life!',
            'cat': 'Electronics',
            'price': 899.99,
            'co2': 315.0, # huge saving for electronics
            'owner_id': 2,
            'images': [
                'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&q=80',
                'https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?auto=format&fit=crop&q=80'
            ]
        },
        {
            'title': 'Vintage Levi 501s',
            'desc': 'Classic denim. Slight fade, incredible character.',
            'cat': 'Clothing',
            'price': 45.00,
            'co2': 33.4, # Cotton production savings
            'owner_id': 3,
            'images': [
                'https://images.unsplash.com/photo-1542272604-787c3835535d?auto=format&fit=crop&q=80',
                'https://images.unsplash.com/photo-1604176354204-9268737828e4?auto=format&fit=crop&q=80'
            ]
        },
        {
            'title': 'Upcycled Teak Coffee Table',
            'desc': 'Hand-restored solid wood table. Stained with eco-friendly wax.',
            'cat': 'Furniture',
            'price': 150.00,
            'co2': 65.0, 
            'owner_id': 2,
            'images': [
                'https://images.unsplash.com/photo-1533090481720-856c6e3c1fdc?auto=format&fit=crop&q=80',
                'https://images.unsplash.com/photo-1505843490538-5133c6c7d0e1?auto=format&fit=crop&q=80'
            ]
        },
        {
            'title': 'Sony Alpha A7III Body Only',
            'desc': 'Upgraded to a new model, passing this legend along. Shutter count ~20k.',
            'cat': 'Electronics',
            'price': 1200.00,
            'co2': 45.0,
            'owner_id': 1,
            'images': [
                'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&q=80',
                'https://images.unsplash.com/photo-1502982720700-baf97d4220a8?auto=format&fit=crop&q=80'
            ]
        },
        {
            'title': 'The Lord of the Rings Collection',
            'desc': 'Read once. Paperbacks in great shape.',
            'cat': 'Books',
            'price': 15.00,
            'co2': 5.0,
            'owner_id': 2,
            'images': [
                'https://images.unsplash.com/photo-1629196914225-ebdd42b6c7c1?auto=format&fit=crop&q=80'
            ]
        },
        {
            'title': 'Bose QuietComfort 35 II',
            'desc': 'Like new noise cancelling headphones.',
            'cat': 'Electronics',
            'price': 120.00,
            'co2': 12.0,
            'owner_id': 3,
            'images': [
                'https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&q=80'
            ]
        }
    ]
    
    for pd in sample_products:
        p = Product(
            owner_id=pd['owner_id'],
            title=pd['title'],
            description=pd['desc'],
            category=pd['cat'],
            price=pd['price'],
            co2_saved_kg=pd['co2']
        )
        db.session.add(p)
        db.session.flush()
        
        for idx, img_url in enumerate(pd['images']):
            db.session.add(ProductImage(
                product_id=p.id,
                image_url=img_url
            ))
            
    db.session.commit()
    print("🌱 Database seeded with EcoFinds products and images!")
