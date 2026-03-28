import uuid

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from app import db
from app.models.user import Usuario, PasswordResetToken
from app.models.financial import Credito
from app.services.email_service import send_reset_email
from flask_wtf.csrf import generate_csrf

api = Blueprint('api', __name__)

@api.route('/csrf-token', methods=['GET'])
def get_csrf_token():
    return jsonify({'csrf_token': generate_csrf()})

@api.route('/forgot_password', methods=['POST'])
def forgot_password_api():
    """API Blueprint independiente para generar el token y enviar correo"""
    data = request.get_json()
    email = data.get('email')
    if not email:
         return jsonify({'error': 'Email is required'}), 400
         
    user = Usuario.query.filter_by(email=email).first()
    if user:
        token_str = str(uuid.uuid4())
        expiration = datetime.utcnow() + timedelta(hours=1)
        token = PasswordResetToken(usuario_id=user.id, token=token_str, fecha_expiracion=expiration)
        db.session.add(token)
        db.session.commit()
        
        send_reset_email(user.email, token_str)
        
    # Siempre respondemos 200 por seguridad (anti-enum)
    return jsonify({'message': 'Si el correo existe, recibirás un enlace de recuperación.'}), 200

@api.route('/score', methods=['GET'])
def get_score_api():
    from flask_login import current_user
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 401
    
    creditos = Credito.query.filter_by(usuario_id=current_user.id).all()
    total_limite = sum(c.limite_credito for c in creditos)
    total_usado = sum(c.deuda_actual for c in creditos)
    
    if total_limite > 0:
        utilizacion = float(total_usado / total_limite)
    else:
        utilizacion = 0

    score = 850 - (utilizacion * 200)
    score = max(400, min(850, score)) # clamping between 400 and 850
    
    return jsonify({
        'score': int(score),
        'utilization': round(utilizacion * 100, 2),
        'total_limit': float(total_limite),
        'total_used': float(total_usado)
    })
