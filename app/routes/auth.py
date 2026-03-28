from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db, bcrypt
from app.models.user import Usuario, PasswordResetToken
from app.forms import RegForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from flask_login import login_user, current_user, logout_user

auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = RegForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = Usuario(
            nombre=form.nombre.data,
            apellidos=form.apellidos.data,
            edad=form.edad.data,
            telefono=form.telefono.data,
            email=form.email.data,
            password_hash=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash('Cuenta creada exitosamente. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
        else:
            flash('Login fallido. Verifica tu correo y contraseña.', 'danger')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


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

    token_obj = PasswordResetToken.query.filter_by(token=token, usado=False).first()
    if not token_obj or token_obj.fecha_expiracion < datetime.utcnow():
        flash('El enlace es inválido o ha expirado.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = Usuario.query.get(token_obj.usuario_id)
        user.password_hash = hashed_password
        token_obj.usado = True
        db.session.commit()
        flash('Tu contraseña ha sido actualizada. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form)