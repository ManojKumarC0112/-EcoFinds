from flask import Blueprint, request, jsonify
from extensions import db
from models import CartItem, Product
from utils.security import jwt_required

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

@cart_bp.route('/add', methods=['POST'])
@jwt_required
def add_to_cart(current_user):
    """Add product to cart using JWT identity implicitly"""
    data = request.get_json() or {}
    product_id = data.get('product_id')
    
    if not product_id:
        return jsonify({'ok': False, 'error': 'product_id required'}), 400
        
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'ok': False, 'error': 'Product not found'}), 404
        
    existing = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        return jsonify({'ok': False, 'error': 'Product already in cart'}), 409
        
    cart_item = CartItem(user_id=current_user.id, product_id=product_id)
    db.session.add(cart_item)
    db.session.commit()
    
    return jsonify({'ok': True, 'cart_item_id': cart_item.id}), 201

@cart_bp.route('/', methods=['GET'])
@jwt_required
def get_cart(current_user):
    """Get cart items securely for logged-in user"""
    cart_items = db.session.query(CartItem, Product).join(
        Product, CartItem.product_id == Product.id
    ).filter(CartItem.user_id == current_user.id).order_by(CartItem.added_at.desc()).all()
    
    results = []
    for cart_item, product in cart_items:
        primary_img = product.images[0].image_url if product.images else 'https://via.placeholder.com/300x200'
        results.append({
            'cart_item_id': cart_item.id,
            'product_id': product.id,
            'title': product.title,
            'price': product.price,
            'image_url': primary_img
        })
        
    return jsonify({'ok': True, 'results': results}), 200

@cart_bp.route('/<int:cart_item_id>', methods=['DELETE'])
@jwt_required
def remove_from_cart(current_user, cart_item_id):
    """Remove item from cart securely"""
    item = CartItem.query.filter_by(id=cart_item_id, user_id=current_user.id).first()
    if not item:
        return jsonify({'ok': False, 'error': 'Cart item not found'}), 404
        
    db.session.delete(item)
    db.session.commit()
    return jsonify({'ok': True}), 200
