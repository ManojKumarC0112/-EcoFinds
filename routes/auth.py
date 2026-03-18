from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import random
from extensions import db
from models import User, OTPRecord
from utils.security import generate_token, jwt_required

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    """Simulate sending an OTP to email or phone"""
    data = request.get_json() or {}
    identifier = str(data.get('identifier', '')).strip().lower()
    
    if not identifier:
        return jsonify({'ok': False, 'error': 'Email or phone number required'}), 400
        
    # Generate random 6-digit OTP
    otp = str(random.randint(100000, 999999))
    
    # In a real application, you would send the SMS/Email here.
    # For resume/portfolio purposes, we print to console to simulate.
    print(f"\n[MOCK EMAIL/SMS] Sending OTP {otp} to {identifier}\n")
    
    # Store OTP
    record = OTPRecord(
        identifier=identifier,
        otp=otp,
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.session.add(record)
    db.session.commit()
    
    return jsonify({
        'ok': True, 
        'message': 'OTP sent successfully (check console limit for demo)',
        # Returning OTP in response purely for testing frontend ease without email backend. 
        # IN PRODUCTION: Remove this property immediately!
        'mock_otp_for_testing': otp
    }), 200

@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP and issue JWT token"""
    data = request.get_json() or {}
    identifier = str(data.get('identifier', '')).strip().lower()
    otp_code = str(data.get('otp', '')).strip()
    
    if not identifier or not otp_code:
        return jsonify({'ok': False, 'error': 'Identifier and OTP required'}), 400
        
    # Find latest correct OTP within expiry
    now = datetime.utcnow()
    valid_record = OTPRecord.query.filter(
        OTPRecord.identifier == identifier,
        OTPRecord.otp == otp_code,
        OTPRecord.expires_at > now
    ).order_by(OTPRecord.created_at.desc()).first()
    
    if not valid_record:
        return jsonify({'ok': False, 'error': 'Invalid or expired OTP'}), 401
        
    # Valid OTP! Check if user exists, if not, register them smoothly.
    user = User.query.filter_by(identifier=identifier).first()
    if not user:
        # Create user
        user = User(identifier=identifier, username=identifier.split('@')[0])
        db.session.add(user)
        db.session.commit()
        
    # Clean up used OTPs
    OTPRecord.query.filter_by(identifier=identifier).delete()
    db.session.commit()
    
    # Generate token
    token = generate_token(user.id)
    
    return jsonify({
        'ok': True,
        'token': token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required
def get_me(current_user):
    """Get current logged-in user details"""
    return jsonify({
        'ok': True,
        'user': current_user.to_dict()
    }), 200
