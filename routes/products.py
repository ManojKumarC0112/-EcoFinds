from flask import Blueprint, request, jsonify
from extensions import db
from models import Product, ProductImage
from utils.security import jwt_required

products_bp = Blueprint('products', __name__, url_prefix='/products')

@products_bp.route('/', methods=['POST'], strict_slashes=False)
@jwt_required
def create_product(current_user):
    """Create a new product listing"""
    data = request.get_json() or {}
    
    title = str(data.get('title', '')).strip()
    category = str(data.get('category', '')).strip()
    price = data.get('price')
    
    if not title or not category or price is None:
        return jsonify({'ok': False, 'error': 'Title, category, and price required'}), 400
        
    try:
        price = float(price)
        if price < 0:
            return jsonify({'ok': False, 'error': 'Price must be positive'}), 400
    except (ValueError, TypeError):
        return jsonify({'ok': False, 'error': 'Invalid price format'}), 400
        
    # Calculate CO2 saved (dummy logic: 15kg for electronics, 5kg for clothes, etc)
    co2 = 15.0
    if 'clothing' in category.lower(): co2 = 5.0
    elif 'furniture' in category.lower(): co2 = 30.0
    
    product = Product(
        owner_id=current_user.id,
        title=title,
        description=str(data.get('description', '')).strip() or None,
        category=category,
        price=price,
        co2_saved_kg=co2
    )
    
    db.session.add(product)
    db.session.flush() # get ID
    
    images = data.get('images', [])
    if images and isinstance(images, list):
        for idx, img_url in enumerate(images):
            db.session.add(ProductImage(
                product_id=product.id,
                image_url=img_url
            ))
            
    db.session.commit()
    return jsonify({'ok': True, 'product_id': product.id}), 201

@products_bp.route('/', methods=['GET'], strict_slashes=False)
def list_products():
    """List products with optional search and filter"""
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    seller_id = request.args.get('seller_id')
    
    query = Product.query
    
    if q: query = query.filter(Product.title.ilike(f'%{q}%'))
    if category and category.lower() != 'all categories':
        query = query.filter(Product.category.ilike(f'%{category}%'))
    if seller_id and seller_id.isdigit():
        query = query.filter(Product.owner_id == int(seller_id))
        
    products = query.order_by(Product.created_at.desc()).limit(100).all()
    return jsonify({'ok': True, 'results': [p.to_list_dict() for p in products]}), 200

@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get rich product details (images, reviews)"""
    product = Product.query.get(product_id)
    if not product: return jsonify({'ok': False, 'error': 'Product not found'}), 404
    
    ret = product.to_dict()
    
    # Bundle recent reviews
    reviews_list = []
    for r in product.reviews[-5:]: # last 5
        reviews_list.append({
            'rating': r.rating,
            'comment': r.comment,
            'user': r.user.username or r.user.identifier.split('@')[0],
            'date': r.created_at.isoformat()
        })
    ret['recent_reviews'] = reviews_list
        
    return jsonify({'ok': True, 'product': ret}), 200

# Optional: Recommendations
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@products_bp.route('/reco', methods=['GET'])
def get_recommendations_ai():
    product_id = request.args.get('product_id')
    if not product_id: return jsonify({'ok': False, 'error': 'product_id required'}), 400
    
    base_product = Product.query.get(product_id)
    if not base_product: return jsonify({'ok': False, 'error': 'Product not found'}), 404

    products = Product.query.filter(Product.id != product_id).all()
    if len(products) < 2: return jsonify({'ok': True, 'results': []}), 200

    product_texts = [p.title + " " + (p.description or "") for p in products]
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(product_texts)
    
    base_text = base_product.title + " " + (base_product.description or "")
    base_vec = tfidf.transform([base_text])
    
    cosine_sim = cosine_similarity(base_vec, tfidf_matrix).flatten()
    top_indices = cosine_sim.argsort()[-6:][::-1]
    
    recommendations = [products[i].to_list_dict() for i in top_indices if cosine_sim[i] > 0.05]
    return jsonify({'ok': True, 'results': recommendations}), 200
