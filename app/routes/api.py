import uuid
from app import csrf
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from app import db
from app.models.user import Usuario, PasswordResetToken
from app.models.financial import Credito
from app.services.email_service import send_reset_email
from flask_wtf.csrf import generate_csrf

from flask import send_file
import io
from app.services.huggingface import generar_imagen




api = Blueprint('api', __name__)


from app import csrf
from flask import send_file, request
import io
from app.services.huggingface import generar_imagen

@api.route("/generate", methods=["POST"])
@csrf.exempt
def generate():
    data = request.get_json()
    prompt = data.get("prompt")

    if not prompt:
        return {"error": "Prompt requerido"}, 400

    imagen = generar_imagen(prompt)

    return send_file(
        io.BytesIO(imagen),
        mimetype='image/png'
    )

@api.route('/csrf-token', methods=['GET'])
def get_csrf_token():
    try:
        return jsonify({'csrf_token': generate_csrf()})
    except Exception as e:
        return jsonify({'error': f'Error al generar token CSRF: {str(e)}'}), 500


@api.route('/forgot_password', methods=['POST'])
def forgot_password_api():
    """API Blueprint independiente para generar el token y enviar correo"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Se requiere un cuerpo JSON válido.'}), 400

        email = data.get('email', '').strip().lower()
        if not email:
            return jsonify({'error': 'El campo email es obligatorio.'}), 400

        # Validar formato de email
        if '@' not in email or '.' not in email:
            return jsonify({'error': 'El formato del correo electrónico no es válido.'}), 400

        user = Usuario.query.filter_by(email=email).first()
        if user:
            # Invalidar tokens anteriores no usados
            old_tokens = PasswordResetToken.query.filter_by(
                usuario_id=user.id, usado=False
            ).all()
            for t in old_tokens:
                t.usado = True

            token_str = str(uuid.uuid4())
            expiration = datetime.utcnow() + timedelta(hours=1)
            token = PasswordResetToken(
                usuario_id=user.id,
                token=token_str,
                fecha_expiracion=expiration
            )
            db.session.add(token)
            db.session.commit()

            send_reset_email(user.email, token_str)

        # Siempre respondemos 200 por seguridad (anti-enum)
        return jsonify({
            'message': 'Si el correo existe en nuestro sistema, recibirás un enlace de recuperación.'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno: {str(e)}'}), 500


@api.route('/score', methods=['GET'])
def get_score_api():
    try:
        from flask_login import current_user
        if not current_user.is_authenticated:
            return jsonify({'error': 'No autorizado. Inicia sesión para ver tu score.'}), 401

        creditos = Credito.query.filter_by(usuario_id=current_user.id).all()
        total_limite = sum(float(c.limite_credito) for c in creditos)
        total_usado = sum(float(c.deuda_actual) for c in creditos)

        if total_limite > 0:
            utilizacion = total_usado / total_limite
        else:
            utilizacion = 0

        score = 850 - (utilizacion * 200)
        score = max(400, min(850, score))  # clamping between 400 and 850

        return jsonify({
            'score': int(score),
            'utilization': round(utilizacion * 100, 2),
            'total_limit': total_limite,
            'total_used': total_usado
        })
    except Exception as e:
        return jsonify({'error': f'Error al calcular el score: {str(e)}'}), 500
