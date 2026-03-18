from flask import Flask, jsonify
from flask_cors import CORS
import os
from datetime import datetime

from extensions import db

# Import blueprints
from routes.auth import auth_bp
from routes.products import products_bp
from routes.cart import cart_bp
from routes.orders import orders_bp
from routes.analytics import analytics_bp

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecofinds_v2.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET'] = os.environ.get('JWT_SECRET', 'super-secret-resume-key')
    
    CORS(app)
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(analytics_bp)
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'ok': True,
            'status': 'EcoFinds v2 API is running (Modular)',
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Seed the database
        from utils.seed import seed_database
        seed_database()
        
        print("🚀 EcoFinds V2 Backend starting...")
        print("🌐 http://localhost:5000")
        app.run(debug=True, port=5000, host='0.0.0.0')