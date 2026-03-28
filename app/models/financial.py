from datetime import datetime
from app import db

class TipoInstitucion(db.Model):
    __tablename__ = 'tipos_institucion'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    instituciones = db.relationship('Institucion', backref='tipo', lazy=True, cascade='all, delete-orphan')

class Institucion(db.Model):
    __tablename__ = 'instituciones'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), unique=True, nullable=False)
    tipo_id = db.Column(db.Integer, db.ForeignKey('tipos_institucion.id', ondelete='CASCADE'), nullable=False)
    creditos = db.relationship('Credito', backref='institucion', lazy=True, cascade='all, delete-orphan')

class Credito(db.Model):
    __tablename__ = 'creditos'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    institucion_id = db.Column(db.Integer, db.ForeignKey('instituciones.id', ondelete='CASCADE'), nullable=False)
    limite_credito = db.Column(db.Numeric(15, 2), nullable=False)
    deuda_actual = db.Column(db.Numeric(15, 2), nullable=False)
    tasa_anual = db.Column(db.Numeric(5, 2), nullable=False)
    pago_minimo = db.Column(db.Numeric(15, 2), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

class CategoriaGasto(db.Model):
    __tablename__ = 'categorias_gasto'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    gastos = db.relationship('Gasto', backref='categoria', lazy=True, cascade='all, delete-orphan')

class Gasto(db.Model):
    __tablename__ = 'gastos'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias_gasto.id', ondelete='CASCADE'), nullable=False)
    descripcion = db.Column(db.String(255), nullable=False)
    monto = db.Column(db.Numeric(15, 2), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
