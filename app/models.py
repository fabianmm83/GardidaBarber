from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from datetime import datetime


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'barbero' o 'cliente'

    citas_agendadas = db.relationship('Cita', foreign_keys='Cita.cliente_id', lazy='dynamic')

    def __repr__(self):
        return f"<User {self.username} - {self.role}>"

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @property
    def is_barbero(self):
        return self.role == 'barbero'  # Devuelve True si el rol es 'barbero'



class Barbero(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    nombre = db.Column(db.String(100), nullable=False)

    user = db.relationship('User', backref=db.backref('barbero', uselist=False))
    citas_asignadas = db.relationship('Cita', foreign_keys='Cita.barbero_id', lazy='dynamic')

    def __repr__(self):
        return f"<Barbero {self.nombre}>"


class Cita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    barbero_id = db.Column(db.Integer, db.ForeignKey('barbero.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fecha_hora = db.Column(db.DateTime, nullable=False)

    barbero = db.relationship('Barbero', foreign_keys=[barbero_id], overlaps="citas_asignadas")
    cliente = db.relationship('User', foreign_keys=[cliente_id], overlaps="citas_agendadas")

    def __repr__(self):
        return f"<Cita {self.id} - Barbero: {self.barbero.nombre} - Cliente: {self.cliente.username} - Fecha: {self.fecha_hora}>"





class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(200))
    precio = db.Column(db.Float, nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)  # Cantidad disponible

    def __repr__(self):
        return f"<Producto {self.nombre} - {self.precio}>"

    def reducir_stock(self, cantidad_vendida):
        if self.cantidad >= cantidad_vendida:
            self.cantidad -= cantidad_vendida
            db.session.commit()
        else:
            raise ValueError("Stock insuficiente")


class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    fecha_venta = db.Column(db.DateTime, default=datetime.utcnow)

    cliente = db.relationship('User', foreign_keys=[cliente_id], backref=db.backref('compras', lazy=True))
    producto = db.relationship('Producto', backref=db.backref('ventas', lazy=True))

    def __repr__(self):
        return f"<Venta {self.id} - {self.cantidad} {self.producto.nombre}>"

    def registrar_venta(self):
        try:
            self.producto.reducir_stock(self.cantidad)
            db.session.add(self)
            db.session.commit()
        except ValueError as e:
            db.session.rollback()
            raise e
