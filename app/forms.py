from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, DecimalField, SelectField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, NumberRange
from app.models.user import Usuario

class RegForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    apellidos = StringField('Apellidos', validators=[DataRequired()])
    edad = IntegerField('Edad', validators=[DataRequired(), NumberRange(min=18, message='Debes tener al menos 18 años')])
    telefono = StringField('Teléfono Celular', validators=[DataRequired()])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Comenzar mi transformación')

    def validate_email(self, email):
        user = Usuario.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Ese correo ya está registrado.')

class LoginForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Ingresar')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    submit = SubmitField('Enviar Enlace')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nueva Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Restablecer Contraseña')

class CreditoForm(FlaskForm):
    institucion_id = SelectField('Institución Financiera', coerce=int, validators=[DataRequired()])
    limite_credito = DecimalField('Límite de Crédito Total', validators=[DataRequired(), NumberRange(min=0)])
    deuda_actual = DecimalField('Deuda Actual', validators=[DataRequired(), NumberRange(min=0)])
    tasa_anual = DecimalField('Tasa Anual (%)', validators=[DataRequired(), NumberRange(min=0)])
    pago_minimo = DecimalField('Pago Mínimo', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Registrar Crédito')

class GastoForm(FlaskForm):
    categoria_id = SelectField('Categoría', coerce=int, validators=[DataRequired()])
    descripcion = StringField('Descripción', validators=[DataRequired()])
    monto = DecimalField('Monto', validators=[DataRequired(), NumberRange(min=0.01)])
    fecha = DateField('Fecha', validators=[DataRequired()])
    submit = SubmitField('Registrar Gasto')

class ProfileForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    apellidos = StringField('Apellidos', validators=[DataRequired()])
    edad = IntegerField('Edad', validators=[DataRequired(), NumberRange(min=18)])
    telefono = StringField('Teléfono Celular')
    submit = SubmitField('Guardar Cambios')
