from datetime import datetime
from extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(120), unique=True, nullable=False) # Email or Phone
    username = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='owner', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'identifier': self.identifier,
            'username': self.username,
            'created_at': self.created_at.isoformat()
        }

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    # Eco-friendly/Carbon tracking metric: estimated kg of CO2 saved vs buying new
    co2_saved_kg = db.Column(db.Float, default=15.0) 
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='product', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        imgs = [img.image_url for img in self.images]
        if not imgs:
            imgs = ['https://via.placeholder.com/600x400?text=EcoFinds+No+Image']
            
        # Calculate rating
        rating = 0
        if self.reviews:
            rating = sum(r.rating for r in self.reviews) / len(self.reviews)

        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'owner_name': self.owner.username if self.owner else 'Unknown',
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'price': self.price,
            'co2_saved_kg': self.co2_saved_kg,
            'created_at': self.created_at.isoformat(),
            'images': imgs,
            'average_rating': round(rating, 1),
            'review_count': len(self.reviews)
        }
        
    def to_list_dict(self):
        imgs = [img.image_url for img in self.images]
        primary_img = imgs[0] if imgs else 'https://via.placeholder.com/300x200?text=EcoFinds'
        
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'title': self.title,
            'category': self.category,
            'price': self.price,
            'image_url': primary_img
        }

class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False) # 1-5
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    total_co2_saved = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default='Pending') # Pending, Shipped, Delivered
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    product_title = db.Column(db.String(120), nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False)

class OTPRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(120), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
