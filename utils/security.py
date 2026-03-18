import jwt
from functools import wraps
from flask import request, jsonify, current_app
from models import User

def generate_token(user_id):
    payload = {
        'user_id': user_id
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET'], algorithm='HS256')

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            parts = request.headers['Authorization'].split()
            if len(parts) == 2 and parts[0] == 'Bearer':
                token = parts[1]
                
        if not token:
            return jsonify({'ok': False, 'error': 'Authentication token is missing. Please log in.'}), 401
            
        try:
            data = jwt.decode(token, current_app.config['JWT_SECRET'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'ok': False, 'error': 'User associated with token not found!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'ok': False, 'error': 'Token has expired!'}), 401
        except Exception as e:
            return jsonify({'ok': False, 'error': 'Token is invalid!'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated
