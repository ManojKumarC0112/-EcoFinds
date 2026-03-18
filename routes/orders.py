from flask import Blueprint, request, jsonify
from extensions import db
from models import CartItem, Product, Order, OrderItem, Review
from utils.security import jwt_required

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

@orders_bp.route('/checkout', methods=['POST'])
@jwt_required
def checkout(current_user):
    """Convert cart into an immutable Order"""
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    if not cart_items:
        return jsonify({'ok': False, 'error': 'Cart is empty'}), 400
        
    total_amount = 0.0
    total_co2 = 0.0
    
    # Calculate totals
    for item in cart_items:
        total_amount += item.product.price
        total_co2 += item.product.co2_saved_kg
        
    # Create Order
    order = Order(
        user_id=current_user.id,
        total_amount=total_amount,
        total_co2_saved=total_co2,
        status='Pending'
    )
    db.session.add(order)
    db.session.flush() # get ID
    
    # Create Order Items and empty cart
    for item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            product_title=item.product.title,
            price_at_purchase=item.product.price
        )
        db.session.add(order_item)
        db.session.delete(item) # remove from cart
        
    db.session.commit()
    
    return jsonify({
        'ok': True, 
        'order_id': order.id,
        'message': f'Order placed successfully! You saved an estimated {total_co2}kg of CO2!'
    }), 201

@orders_bp.route('/', methods=['GET'])
@jwt_required
def get_orders(current_user):
    """View order history"""
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    results = []
    for o in orders:
        results.append({
            'order_id': o.id,
            'amount': o.total_amount,
            'co2_saved': o.total_co2_saved,
            'status': o.status,
            'date': o.created_at.isoformat(),
            'items': [i.product_title for i in o.items]
        })
    return jsonify({'ok': True, 'results': results}), 200

@orders_bp.route('/products/<int:product_id>/review', methods=['POST'])
@jwt_required
def add_review(current_user, product_id):
    """Add a review for a purchased product"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'ok': False, 'error': 'Product not found'}), 404
        
    # Optional Check: Only allow if user actually ordered it
    # We will enforce this for quality
    has_ordered = OrderItem.query.join(Order).filter(
        Order.user_id == current_user.id,
        OrderItem.product_id == product_id
    ).first()
    
    if not has_ordered:
        return jsonify({'ok': False, 'error': 'You must purchase this product before reviewing.'}), 403
        
    data = request.get_json() or {}
    rating = data.get('rating')
    comment = str(data.get('comment', '')).strip()
    
    if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({'ok': False, 'error': 'Rating must be integer 1-5'}), 400
        
    existing = Review.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        existing.rating = rating
        existing.comment = comment
    else:
        r = Review(user_id=current_user.id, product_id=product_id, rating=rating, comment=comment)
        db.session.add(r)
        
    db.session.commit()
    return jsonify({'ok': True, 'message': 'Review submitted successfully!'}), 201
