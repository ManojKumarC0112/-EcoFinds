from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Load model & tokenizer once when server starts
model_name = "microsoft/DialoGPT-medium"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Load model & tokenizer once when server starts
model_name = "microsoft/DialoGPT-medium"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)


app = Flask( __name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecofinds.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable CORS for local development
CORS(app)

db = SQLAlchemy(app)

# ================================
# MODELS
# ================================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username
        }

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'price': self.price,
            'image_url': self.image_url or 'https://via.placeholder.com/300x200?text=EcoFinds'
        }
    
    def to_list_dict(self):
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'title': self.title,
            'category': self.category,
            'price': self.price,
            'image_url': self.image_url or 'https://via.placeholder.com/300x200?text=EcoFinds'
        }

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', backref='cart_items')

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', backref='purchases')

# ================================
# HELPER FUNCTIONS
# ================================

def get_json_data(required_fields):
    """Get JSON data and check for required fields"""
    data = request.get_json(silent=True) or {}
    missing = []
    for field in required_fields:
        if field not in data or (isinstance(data[field], str) and not data[field].strip()):
            missing.append(field)
    return data, missing

def validate_user_exists(user_id):
    """Check if user exists"""
    try:
        user_id = int(user_id)
        return User.query.get(user_id) is not None
    except (ValueError, TypeError):
        return False

# ================================
# AUTH ENDPOINTS (Member A)
# ================================

@app.route('/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data, missing = get_json_data(['email', 'password'])
        if missing:
            return jsonify({
                'ok': False, 
                'error': f"Missing required fields: {', '.join(missing)}"
            }), 400
        
        email = str(data['email']).strip().lower()
        password = str(data['password']).strip()
        username = str(data.get('username', '')).strip() or None
        
        # Validate email format (basic)
        if '@' not in email or '.' not in email:
            return jsonify({'ok': False, 'error': 'Invalid email format'}), 400
        
        # Validate password length
        if len(password) < 6:
            return jsonify({'ok': False, 'error': 'Password must be at least 6 characters'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'ok': False, 'error': 'Email already registered'}), 409
        
        # Create new user
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            username=username
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'ok': True,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'ok': False, 
            'error': 'Registration failed',
            'detail': str(e)
        }), 500

@app.route('/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data, missing = get_json_data(['email', 'password'])
        if missing:
            return jsonify({
                'ok': False, 
                'error': f"Missing required fields: {', '.join(missing)}"
            }), 400
        
        email = str(data['email']).strip().lower()
        password = str(data['password']).strip()
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({
                'ok': False, 
                'error': 'Invalid email or password'
            }), 401
        
        return jsonify({
            'ok': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'ok': False, 
            'error': 'Login failed',
            'detail': str(e)
        }), 500

@app.route('/user/update', methods=['POST'])
def user_update():
    """Update user profile"""
    try:
        data, missing = get_json_data(['user_id'])
        if missing:
            return jsonify({
                'ok': False, 
                'error': f"Missing required fields: {', '.join(missing)}"
            }), 400
        
        user_id = int(data['user_id'])
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'ok': False, 'error': 'User not found'}), 404
        
        # Update username if provided
        if 'username' in data:
            username = str(data['username']).strip() or None
            user.username = username
        
        db.session.commit()
        
        return jsonify({
            'ok': True,
            'user': user.to_dict()
        }), 200
        
    except ValueError:
        return jsonify({'ok': False, 'error': 'Invalid user_id'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'ok': False, 
            'error': 'Update failed',
            'detail': str(e)
        }), 500

# ================================
# PRODUCT ENDPOINTS (Member B)
# ================================

@app.route('/products', methods=['POST'])
def create_product():
    """Create a new product listing"""
    try:
        data, missing = get_json_data(['owner_id', 'title', 'category', 'price'])
        if missing:
            return jsonify({
                'ok': False,
                'error': f"Missing required fields: {', '.join(missing)}"
            }), 400
        
        owner_id = int(data['owner_id'])
        
        # Validate user exists
        if not validate_user_exists(owner_id):
            return jsonify({'ok': False, 'error': 'Invalid owner_id'}), 400
        
        # Validate price
        try:
            price = float(data['price'])
            if price < 0:
                return jsonify({'ok': False, 'error': 'Price must be positive'}), 400
        except (ValueError, TypeError):
            return jsonify({'ok': False, 'error': 'Invalid price format'}), 400
        
        # Create product
        product = Product(
            owner_id=owner_id,
            title=str(data['title']).strip(),
            description=str(data.get('description', '')).strip() or None,
            category=str(data['category']).strip(),
            price=price,
            image_url=str(data.get('image_url', '')).strip() or None
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'ok': True,
            'product_id': product.id
        }), 201
        
    except ValueError:
        return jsonify({'ok': False, 'error': 'Invalid data format'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'ok': False,
            'error': 'Failed to create product',
            'detail': str(e)
        }), 500

@app.route('/products', methods=['GET'])
def list_products():
    """List products with optional search and filter"""
    try:
        q = request.args.get('q', '').strip()
        category = request.args.get('category', '').strip()
        
        query = Product.query
        
        # Apply search filter
        if q:
            query = query.filter(Product.title.ilike(f'%{q}%'))
        
        # Apply category filter
        if category and category.lower() != 'all categories':
            query = query.filter(Product.category.ilike(f'%{category}%'))
        
        # Order by newest first and limit results
        products = query.order_by(Product.created_at.desc()).limit(100).all()
        
        return jsonify({
            'ok': True,
            'results': [product.to_list_dict() for product in products]
        }), 200
        
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': 'Failed to fetch products',
            'detail': str(e)
        }), 500

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get product details"""
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'ok': False, 'error': 'Product not found'}), 404
        
        return jsonify({
            'ok': True,
            'product': product.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': 'Failed to fetch product',
            'detail': str(e)
        }), 500

@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update product"""
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'ok': False, 'error': 'Product not found'}), 404
        
        data = request.get_json(silent=True) or {}
        
        # Update fields if provided
        if 'title' in data:
            product.title = str(data['title']).strip()
        if 'description' in data:
            product.description = str(data['description']).strip() or None
        if 'category' in data:
            product.category = str(data['category']).strip()
        if 'price' in data:
            try:
                price = float(data['price'])
                if price < 0:
                    return jsonify({'ok': False, 'error': 'Price must be positive'}), 400
                product.price = price
            except (ValueError, TypeError):
                return jsonify({'ok': False, 'error': 'Invalid price format'}), 400
        if 'image_url' in data:
            product.image_url = str(data['image_url']).strip() or None
        
        db.session.commit()
        
        return jsonify({'ok': True}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'ok': False,
            'error': 'Failed to update product',
            'detail': str(e)
        }), 500

@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete product"""
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'ok': False, 'error': 'Product not found'}), 404
        
        # Remove from carts first
        CartItem.query.filter_by(product_id=product_id).delete()
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({'ok': True}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'ok': False,
            'error': 'Failed to delete product',
            'detail': str(e)
        }), 500

# ================================
# CART & PURCHASE ENDPOINTS (Member C)
# ================================

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    """Add product to cart"""
    try:
        data, missing = get_json_data(['user_id', 'product_id'])
        if missing:
            return jsonify({
                'ok': False,
                'error': f"Missing required fields: {', '.join(missing)}"
            }), 400
        
        user_id = int(data['user_id'])
        product_id = int(data['product_id'])
        
        # Validate user and product exist
        if not validate_user_exists(user_id):
            return jsonify({'ok': False, 'error': 'Invalid user_id'}), 400
        
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'ok': False, 'error': 'Product not found'}), 404
        
        # Check if already in cart
        existing = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
        if existing:
            return jsonify({'ok': False, 'error': 'Product already in cart'}), 409
        
        # Add to cart
        cart_item = CartItem(user_id=user_id, product_id=product_id)
        db.session.add(cart_item)
        db.session.commit()
        
        return jsonify({
            'ok': True,
            'cart_item_id': cart_item.id
        }), 201
        
    except ValueError:
        return jsonify({'ok': False, 'error': 'Invalid data format'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'ok': False,
            'error': 'Failed to add to cart',
            'detail': str(e)
        }), 500

@app.route('/cart', methods=['GET'])
def get_cart():
    """Get user's cart items"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'ok': False, 'error': 'user_id parameter required'}), 400
        
        user_id = int(user_id)
        
        if not validate_user_exists(user_id):
            return jsonify({'ok': False, 'error': 'Invalid user_id'}), 400
        
        # Get cart items with product details
        cart_items = db.session.query(CartItem, Product).join(
            Product, CartItem.product_id == Product.id
        ).filter(CartItem.user_id == user_id).order_by(CartItem.added_at.desc()).all()
        
        results = []
        for cart_item, product in cart_items:
            results.append({
                'cart_item_id': cart_item.id,
                'product_id': product.id,
                'title': product.title,
                'price': product.price,
                'image_url': product.image_url or 'https://via.placeholder.com/300x200?text=EcoFinds'
            })
        
        return jsonify({
            'ok': True,
            'results': results
        }), 200
        
    except ValueError:
        return jsonify({'ok': False, 'error': 'Invalid user_id format'}), 400
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': 'Failed to fetch cart',
            'detail': str(e)
        }), 500

@app.route('/purchase', methods=['POST'])
def purchase_cart():
    """Purchase all items in cart"""
    try:
        data, missing = get_json_data(['user_id'])
        if missing:
            return jsonify({
                'ok': False,
                'error': f"Missing required fields: {', '.join(missing)}"
            }), 400
        
        user_id = int(data['user_id'])
        
        if not validate_user_exists(user_id):
            return jsonify({'ok': False, 'error': 'Invalid user_id'}), 400
        
        # Get all cart items for user
        cart_items = CartItem.query.filter_by(user_id=user_id).all()
        
        if not cart_items:
            return jsonify({'ok': False, 'error': 'Cart is empty'}), 400
        
        # Create purchase records
        purchased_count = 0
        for cart_item in cart_items:
            purchase = Purchase(
                user_id=user_id,
                product_id=cart_item.product_id
            )
            db.session.add(purchase)
            db.session.delete(cart_item)
            purchased_count += 1
        
        db.session.commit()
        
        return jsonify({
            'ok': True,
            'purchased': purchased_count
        }), 200
        
    except ValueError:
        return jsonify({'ok': False, 'error': 'Invalid user_id format'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'ok': False,
            'error': 'Purchase failed',
            'detail': str(e)
        }), 500

@app.route('/purchases', methods=['GET'])
def get_purchases():
    """Get user's purchase history"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'ok': False, 'error': 'user_id parameter required'}), 400
        
        user_id = int(user_id)
        
        if not validate_user_exists(user_id):
            return jsonify({'ok': False, 'error': 'Invalid user_id'}), 400
        
        # Get purchase history with product details
        purchases = db.session.query(Purchase, Product).join(
            Product, Purchase.product_id == Product.id
        ).filter(Purchase.user_id == user_id).order_by(Purchase.purchased_at.desc()).all()
        
        results = []
        for purchase, product in purchases:
            results.append({
                'purchase_id': purchase.id,
                'product_id': product.id,
                'title': product.title,
                'price': product.price,
                'image_url': product.image_url or 'https://via.placeholder.com/300x200?text=EcoFinds',
                'purchased_at': purchase.purchased_at.isoformat()
            })
        
        return jsonify({
            'ok': True,
            'results': results
        }), 200
        
    except ValueError:
        return jsonify({'ok': False, 'error': 'Invalid user_id format'}), 400
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': 'Failed to fetch purchases',
            'detail': str(e)
        }), 500

# ================================
# OPTIONAL: RECOMMENDATIONS (Member C)
# ================================

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@app.route('/products/reco', methods=['GET'])
def get_recommendations_ai():
    """Get AI-powered product recommendations based on content similarity"""
    try:
        product_id = request.args.get('product_id')
        if not product_id:
            return jsonify({'ok': False, 'error': 'product_id parameter required'}), 400
        
        product_id = int(product_id)
        base_product = Product.query.get(product_id)
        if not base_product:
            return jsonify({'ok': False, 'error': 'Product not found'}), 404

        # Get all products excluding the base product itself
        products = Product.query.filter(Product.id != product_id).all()
        if not products:
            return jsonify({'ok': True, 'results': []}), 200

        # Build corpus for TF-IDF (title + description)
        product_texts = [p.title + " " + (p.description or "") for p in products]
        tfidf = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf.fit_transform(product_texts)
        
        # Base product vector
        base_text = base_product.title + " " + (base_product.description or "")
        base_vec = tfidf.transform([base_text])
        
        # Compute cosine similarity
        cosine_sim = cosine_similarity(base_vec, tfidf_matrix).flatten()
        
        # Get top 6 similar products
        top_indices = cosine_sim.argsort()[-6:][::-1]
        recommendations = [products[i].to_list_dict() for i in top_indices]

        return jsonify({
            'ok': True,
            'results': recommendations
        }), 200

    except Exception as e:
        return jsonify({
            'ok': False,
            'error': 'Failed to fetch recommendations',
            'detail': str(e)
        }), 500


# ================================
# UTILITY ENDPOINTS
# ================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'ok': True,
        'status': 'EcoFinds API is running',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

# ================================
# INITIALIZE DATABASE
# ================================

def init_sample_data():
    """Initialize with sample data for demo"""
    if User.query.count() == 0:
        # Create sample users
        users = [
            User(email='demo@ecofinds.com', 
                 password_hash=generate_password_hash('demo123'), 
                 username='Demo User'),
            User(email='seller@ecofinds.com', 
                 password_hash=generate_password_hash('seller123'), 
                 username='Eco Seller')
        ]
        
        for user in users:
            db.session.add(user)
        
        db.session.commit()
        
        # Create sample products
        categories = ['Electronics', 'Clothing', 'Books', 'Furniture', 'Sports']
        sample_products = [
            {'title': 'Vintage Laptop', 'category': 'Electronics', 'price': 299.99, 'description': 'Well-maintained laptop, perfect for students'},
            {'title': 'Designer Jacket', 'category': 'Clothing', 'price': 89.99, 'description': 'Stylish jacket in excellent condition'},
            {'title': 'Programming Books Set', 'category': 'Books', 'price': 45.50, 'description': 'Complete set of programming reference books'},
            {'title': 'Wooden Coffee Table', 'category': 'Furniture', 'price': 120.00, 'description': 'Solid wood coffee table, minor scratches'},
            {'title': 'Tennis Racket', 'category': 'Sports', 'price': 75.00, 'description': 'Professional tennis racket, barely used'}
        ]
        
        for i, product_data in enumerate(sample_products):
            product = Product(
                owner_id=1 if i % 2 == 0 else 2,
                **product_data
            )
            db.session.add(product)
        
        db.session.commit()
        print("✅ Sample data created!")

with app.app_context():
    db.create_all()
    init_sample_data()
    print("🗃  Database tables created successfully!")
# ================================
# CHATBOT ENDPOINTS
# ================================
@app.route('/chatbot', methods=['POST'])
def chatbot():
    try:
        data = request.get_json()
        user_query = data.get('query')
        if not user_query:
            return jsonify({'ok': False, 'error': 'query field required'}), 400

        # Encode user input
        new_input_ids = tokenizer.encode(user_query + tokenizer.eos_token, return_tensors='pt')

        # Generate a response
        chat_history_ids = model.generate(
            new_input_ids,
            max_length=200,
            pad_token_id=tokenizer.eos_token_id,
            no_repeat_ngram_size=3,
            do_sample=True,
            top_k=50,
            top_p=0.95,
            temperature=0.7
        )

        # Decode response
        response = tokenizer.decode(chat_history_ids[:, new_input_ids.shape[-1]:][0], skip_special_tokens=True)

        return jsonify({'ok': True, 'response': response}), 200

    except Exception as e:
        return jsonify({'ok': False, 'error': 'Failed to get AI response', 'detail': str(e)}), 500


if __name__ == '__main__':
    print("🚀 EcoFinds Backend Server Starting...")
    print("📍 Available endpoints:")
    print("   POST /auth/register - Register new user")
    print("   POST /auth/login - Login user") 
    print("   POST /user/update - Update user profile")
    print("   POST /products - Create product listing")
    print("   GET /products - List products (with search & filter)")
    print("   GET /products/<id> - Get product details")
    print("   PUT /products/<id> - Update product")
    print("   DELETE /products/<id> - Delete product")
    print("   POST /cart/add - Add to cart")
    print("   GET /cart?user_id= - Get cart items")
    print("   POST /purchase - Purchase cart items")
    print("   GET /purchases?user_id= - Get purchase history")
    print("   GET /products/reco?product_id= - Get recommendations")
    print("   GET /health - Health check")
    print("\n🌐 Server running at: http://localhost:5000")
    print("🔧 CORS enabled for frontend integration")
    app.run(debug=True, port=5000, host='0.0.0.0')