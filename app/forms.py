import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, DecimalField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, NumberRange, Length, Regexp
from app.models.user import Usuario


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDADORES PERSONALIZADOS
# ═══════════════════════════════════════════════════════════════════════════════

def validar_solo_letras(form, field):
    """Valida que el campo contenga solo letras, espacios y acentos."""
    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$', field.data):
        raise ValidationError(
            'Este campo solo puede contener letras y espacios. '
            'No se permiten números ni caracteres especiales.'
        )


def validar_email_gmail(form, field):
    """Valida que el email sea @gmail.com."""
    email = field.data.lower().strip()
    if not email.endswith('@gmail.com'):
        raise ValidationError(
            'Solo se permiten correos con dominio @gmail.com. '
            'Ejemplo: tu_nombre@gmail.com'
        )


def validar_password_segura(form, field):
    """Valida los requisitos mínimos de seguridad de la contraseña."""
    password = field.data
    errores = []

    if len(password) < 8:
        errores.append('al menos 8 caracteres')
    if not re.search(r'[A-Z]', password):
        errores.append('al menos una letra mayúscula')
    if not re.search(r'[a-z]', password):
        errores.append('al menos una letra minúscula')
    if not re.search(r'[0-9]', password):
        errores.append('al menos un número')

    if errores:
        raise ValidationError(
            'La contraseña debe contener: ' + ', '.join(errores) + '.'
        )


def validar_telefono(form, field):
    """Valida que el teléfono contenga solo dígitos y tenga 10 dígitos."""
    if field.data:
        digitos = re.sub(r'[\s\-\(\)\+]', '', field.data)
        if not digitos.isdigit():
            raise ValidationError('El teléfono solo puede contener números.')
        if len(digitos) < 10 or len(digitos) > 15:
            raise ValidationError('El teléfono debe tener entre 10 y 15 dígitos.')


# ═══════════════════════════════════════════════════════════════════════════════
# FORMULARIOS
# ═══════════════════════════════════════════════════════════════════════════════

class RegForm(FlaskForm):
    nombre = StringField('Nombre', validators=[
        DataRequired(message='El nombre es obligatorio.'),
        Length(min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres.'),
        validar_solo_letras
    ])
    apellidos = StringField('Apellidos', validators=[
        DataRequired(message='Los apellidos son obligatorios.'),
        Length(min=2, max=100, message='Los apellidos deben tener entre 2 y 100 caracteres.'),
        validar_solo_letras
    ])
    edad = IntegerField('Edad', validators=[
        DataRequired(message='La edad es obligatoria.'),
        NumberRange(min=18, max=125, message='La edad debe estar entre 18 y 125 años.')
    ])
    telefono = StringField('Teléfono Celular', validators=[
        DataRequired(message='El teléfono es obligatorio.'),
        validar_telefono
    ])
    email = StringField('Correo Electrónico', validators=[
        DataRequired(message='El correo electrónico es obligatorio.'),
        Email(message='Ingresa un correo electrónico válido.'),
        validar_email_gmail
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es obligatoria.'),
        validar_password_segura
    ])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(message='Debes confirmar tu contraseña.'),
        EqualTo('password', message='Las contraseñas no coinciden.')
    ])
    submit = SubmitField('Comenzar mi transformación')

    def validate_email(self, email):
        user = Usuario.query.filter_by(email=email.data.lower().strip()).first()
        if user:
            raise ValidationError(
                'Este correo ya está registrado. '
                'Intenta iniciar sesión o usa otro correo @gmail.com.'
            )


class LoginForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[
        DataRequired(message='El correo electrónico es obligatorio.'),
        Email(message='Ingresa un correo electrónico válido.')
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es obligatoria.')
    ])
    submit = SubmitField('Ingresar')


class ForgotPasswordForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[
        DataRequired(message='El correo electrónico es obligatorio.'),
        Email(message='Ingresa un correo electrónico válido.')
    ])
    submit = SubmitField('Enviar Enlace')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nueva Contraseña', validators=[
        DataRequired(message='La contraseña es obligatoria.'),
        validar_password_segura
    ])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(message='Debes confirmar tu contraseña.'),
        EqualTo('password', message='Las contraseñas no coinciden.')
    ])
    submit = SubmitField('Restablecer Contraseña')


class CreditoForm(FlaskForm):
    institucion_id = SelectField('Institución Financiera', coerce=int, validators=[
        DataRequired(message='Selecciona una institución financiera.')
    ])
    limite_credito = DecimalField('Límite de Crédito Total', validators=[
        DataRequired(message='El límite de crédito es obligatorio.'),
        NumberRange(min=0, message='El límite de crédito no puede ser negativo.')
    ])
    deuda_actual = DecimalField('Deuda Actual', validators=[
        DataRequired(message='La deuda actual es obligatoria.'),
        NumberRange(min=0, message='La deuda actual no puede ser negativa.')
    ])
    tasa_anual = DecimalField('Tasa Anual (%)', validators=[
        DataRequired(message='La tasa anual es obligatoria.'),
        NumberRange(min=0, max=100, message='La tasa anual debe estar entre 0% y 100%.')
    ])
    pago_minimo = DecimalField('Pago Mínimo', validators=[
        DataRequired(message='El pago mínimo es obligatorio.'),
        NumberRange(min=0, message='El pago mínimo no puede ser negativo.')
    ])
    submit = SubmitField('Registrar Crédito')


class GastoForm(FlaskForm):
    descripcion = StringField('Descripción', validators=[
        DataRequired(message='La descripción del gasto es obligatoria.'),
        Length(min=3, max=255, message='La descripción debe tener entre 3 y 255 caracteres.')
    ])
    monto = DecimalField('Monto', validators=[
        DataRequired(message='El monto del gasto es obligatorio.'),
        NumberRange(min=0.01, message='El monto debe ser mayor a $0.00.')
    ])
    fecha = DateField('Fecha', validators=[
        DataRequired(message='La fecha del gasto es obligatoria.')
    ])
    submit = SubmitField('Registrar Gasto')


class ProfileForm(FlaskForm):
    nombre = StringField('Nombre', validators=[
        DataRequired(message='El nombre es obligatorio.'),
        Length(min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres.'),
        validar_solo_letras
    ])
    apellidos = StringField('Apellidos', validators=[
        DataRequired(message='Los apellidos son obligatorios.'),
        Length(min=2, max=100, message='Los apellidos deben tener entre 2 y 100 caracteres.'),
        validar_solo_letras
    ])
    edad = IntegerField('Edad', validators=[
        DataRequired(message='La edad es obligatoria.'),
        NumberRange(min=18, max=125, message='La edad debe estar entre 18 y 125 años.')
    ])
    telefono = StringField('Teléfono Celular', validators=[
        validar_telefono
    ])
    submit = SubmitField('Guardar Cambios')
