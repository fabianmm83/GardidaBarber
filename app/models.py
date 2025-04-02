from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from flask_wtf import FlaskForm
from datetime import datetime
from wtforms.validators import DataRequired, Email
from wtforms import StringField, BooleanField, SubmitField

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='cliente')
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)

    # Relaciones
    citas_como_cliente = db.relationship('Cita', 
                                       foreign_keys='Cita.cliente_id', 
                                       back_populates='cliente',
                                       lazy='dynamic')
    
    ventas_como_cliente = db.relationship('Venta', 
                                        foreign_keys='Venta.cliente_id', 
                                        back_populates='cliente',
                                        lazy=True)
    
    # Relaciones de perfil
    admin_profile = db.relationship('Admin', 
                                  back_populates='user', 
                                  uselist=False,
                                  cascade='all, delete-orphan')
    
    barbero_profile = db.relationship('Barbero', 
                                    back_populates='user', 
                                    uselist=False,
                                    cascade='all, delete-orphan')

    def __repr__(self):
        return f"<User {self.username} - {self.role}>"

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_barbero(self):
        return self.role == 'barbero'

    @property
    def is_cliente(self):
        return self.role == 'cliente'




class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    nivel_acceso = db.Column(db.Integer, default=1)
    permisos_especiales = db.Column(db.String(200))

    user = db.relationship('User', back_populates='admin_profile')

    def __repr__(self):
        return f"<Admin {self.user.username} - Nivel {self.nivel_acceso}>"

class Barbero(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    nombre = db.Column(db.String(50), nullable=False)
    apellido = db.Column(db.String(50), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    correo = db.Column(db.String(100), nullable=False, unique=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)

    # Relaciones
    citas = db.relationship('Cita', 
                          foreign_keys='Cita.barbero_id',
                          back_populates='barbero',
                          lazy='dynamic')
    
    user = db.relationship('User', back_populates='barbero_profile')

    def __repr__(self):
        return f"<Barbero {self.nombre} {self.apellido}>"

class Cita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    barbero_id = db.Column(db.Integer, db.ForeignKey('barbero.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fecha_hora = db.Column(db.DateTime, nullable=False)
    servicio = db.Column(db.String(150))
    estado = db.Column(db.String(50), default='pendiente')
    notas = db.Column(db.Text)

    # Relaciones
    barbero = db.relationship('Barbero', back_populates='citas')
    cliente = db.relationship('User', back_populates='citas_como_cliente')

    def __repr__(self):
        return f"<Cita {self.id} - {self.servicio} - {self.estado}>"

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Float, nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=0)
    categoria = db.Column(db.String(50))
    imagen = db.Column(db.String(200))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación con ventas
    ventas = db.relationship('Venta', back_populates='producto', lazy=True)

    def __repr__(self):
        return f"<Producto {self.nombre} - ${self.precio}>"

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
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    precio_unitario = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    fecha_venta = db.Column(db.DateTime, default=datetime.utcnow)
    metodo_pago = db.Column(db.String(50))

    # Relaciones
    producto = db.relationship('Producto', back_populates='ventas')
    cliente = db.relationship('User', back_populates='ventas_como_cliente')

    def __repr__(self):
        return f"<Venta {self.id} - {self.producto.nombre} x{self.cantidad}>"

    def registrar_venta(self):
        try:
            self.producto.reducir_stock(self.cantidad)
            self.precio_unitario = self.producto.precio
            self.total = self.precio_unitario * self.cantidad
            db.session.add(self)
            db.session.commit()
            return True
        except ValueError as e:
            db.session.rollback()
            raise e




class EditarUsuarioForm(FlaskForm):
    username = StringField('Nombre de usuario', validators=[DataRequired()])
    email = StringField('Correo electrónico', validators=[DataRequired(), Email()])
    role = StringField('Rol', validators=[DataRequired()])
    activo = BooleanField('Activo')
    submit = SubmitField('Guardar cambios')

class Configuracion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.Text, nullable=False)
    descripcion = db.Column(db.Text)

    def __repr__(self):
        return f"<Configuracion {self.nombre}={self.valor}>"