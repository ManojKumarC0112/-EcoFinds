from flask import Blueprint, jsonify
from sqlalchemy import func
from extensions import db
from models import Order, OrderItem, Product
from utils.security import jwt_required

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/seller', methods=['GET'])
@jwt_required
def seller_dashboard(current_user):
    """Get analytics for the current seller's products (for Chart.js)"""
    
    # Total products listed
    total_listings = Product.query.filter_by(owner_id=current_user.id).count()
    
    # Items sold (where the product owner is current_user)
    sold_items_query = db.session.query(OrderItem).join(Product, OrderItem.product_id == Product.id).filter(Product.owner_id == current_user.id)
    total_sales = sold_items_query.count()
    
    # Total Revenue
    total_revenue = sum(item.price_at_purchase for item in sold_items_query.all())
    
    # Time-series data (e.g., sales grouped by date)
    # Using simple Python grouping since SQLite date functions can be finicky cross-platform
    sales_by_date = {}
    for item in sold_items_query.join(Order).all():
        date_str = item.order.created_at.strftime('%Y-%m-%d')
        if date_str not in sales_by_date:
            sales_by_date[date_str] = 0.0
        sales_by_date[date_str] += item.price_at_purchase
        
    dates = sorted(list(sales_by_date.keys()))
    revenues = [sales_by_date[d] for d in dates]
    
    return jsonify({
        'ok': True,
        'metrics': {
            'total_listings': total_listings,
            'total_sales': total_sales,
            'total_revenue': round(total_revenue, 2)
        },
        'chart_data': {
            'labels': dates,
            'data': revenues
        }
    }), 200
