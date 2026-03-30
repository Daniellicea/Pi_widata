from datetime import datetime
# AÑADIMOS make_response A LAS IMPORTACIONES DE FLASK
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, make_response
from app import db, bcrypt
from app.models.user import Usuario, PasswordResetToken
from app.forms import RegForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
# AÑADIMOS login_required A LAS IMPORTACIONES DE FLASK_LOGIN
from flask_login import login_user, current_user, logout_user, login_required

auth = Blueprint('auth', __name__, url_prefix='/auth')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = RegForm()
    if form.validate_on_submit():
        try:
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user = Usuario(
                nombre=form.nombre.data.strip(),
                apellidos=form.apellidos.data.strip(),
                edad=form.edad.data,
                telefono=form.telefono.data.strip() if form.telefono.data else None,
                email=form.email.data.lower().strip(),
                password_hash=hashed_password
            )
            db.session.add(user)
            db.session.commit()
            flash(' Cuenta creada exitosamente. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f' Error al crear la cuenta: {str(e)}', 'danger')
    return render_template('auth/register.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = Usuario.query.filter_by(email=form.email.data.lower().strip()).first()
            if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
                login_user(user, remember=True)
                next_page = request.args.get('next')
                flash(f' ¡Bienvenido de vuelta, {user.nombre}!', 'success')
                return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
            else:
                flash(' Login fallido. Verifica que tu correo sea @gmail.com y la contraseña sea correcta.', 'danger')
        except Exception as e:
            flash(f' Error interno al iniciar sesión: {str(e)}', 'danger')
    return render_template('auth/login.html', form=form)


# ==========================================
# FUNCIÓN DE LOGOUT ACTUALIZADA Y MEJORADA
# ==========================================
@auth.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Cierre de sesión: Destrucción total de sesión y cookies."""
    # 1. Matar la sesión en Flask-Login
    logout_user()
    
    # 2. Vaciar el diccionario de la sesión de Flask por completo
    for key in list(session.keys()):
        session.pop(key)
    session.clear()

    # 3. Preparar la redirección al login
    response = make_response(redirect(url_for('auth.login')))
    
    # 4. EXTERMINAR LAS COOKIES FÍSICAMENTE (Aquí está la clave)
    response.set_cookie('session', '', expires=0)
    response.set_cookie('remember_token', '', expires=0)
    
    # 5. Matar la caché del navegador
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    flash('Sesión cerrada definitivamente.', 'success')
    return response
@auth.route('/forgot_password', methods=['GET'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = ForgotPasswordForm()
    return render_template('auth/forgot_password.html', form=form)


@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if not token or len(token) < 10:
        flash(' El enlace de recuperación no es válido.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    token_obj = PasswordResetToken.query.filter_by(token=token, usado=False).first()
    if not token_obj or token_obj.fecha_expiracion < datetime.utcnow():
        flash(' El enlace es inválido o ha expirado. Solicita uno nuevo.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        try:
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user = Usuario.query.get(token_obj.usuario_id)
            if not user:
                flash(' Usuario no encontrado.', 'danger')
                return redirect(url_for('auth.forgot_password'))

            user.password_hash = hashed_password
            token_obj.usado = True
            db.session.commit()
            flash('✅ Tu contraseña ha sido actualizada. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f' Error al restablecer la contraseña: {str(e)}', 'danger')

    return render_template('auth/reset_password.html', form=form)