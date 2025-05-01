from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from flask_wtf import FlaskForm
from datetime import datetime
from wtforms.validators import DataRequired, Email
from wtforms import StringField, BooleanField, SubmitField



class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    nombre = db.Column(db.String(64))
    apellido = db.Column(db.String(64))
    
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='cliente')
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)
    is_guest = db.Column(db.Boolean, default=False)
    phone = db.Column(db.String(20))

    # Relaciones
    citas_como_cliente = db.relationship('Cita', 
                                      foreign_keys='Cita.cliente_id', 
                                      back_populates='cliente',
                                      lazy='dynamic')
    
    citas_como_administrador = db.relationship('Cita',
                                            foreign_keys='Cita.admin_id',
                                            back_populates='administrador',
                                            lazy='dynamic')
    
   
    
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
    
    def ensure_barbero_profile(self):
        """Asegura que el usuario admin tenga un perfil de barbero"""
        if self.is_admin and not self.barbero_profile:
            barbero = Barbero(
                user_id=self.id,
                nombre=self.username,
                apellido="",  # O algún valor por defecto
                telefono=self.phone or "",
                correo=self.email,
                activo=True
            )
            db.session.add(barbero)
            db.session.commit()
            return barbero
        return self.barbero_profile

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
    __tablename__ = 'admin'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    nivel_acceso = db.Column(db.Integer, default=1)
    permisos_especiales = db.Column(db.String(200))

    # Relación con User
    user = db.relationship('User', back_populates='admin_profile')

    def __repr__(self):
        return f"<Admin {self.user.username if self.user else 'Sin usuario'} - Nivel {self.nivel_acceso}>"

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
    __tablename__ = 'citas'
    
    id = db.Column(db.Integer, primary_key=True)
    barbero_id = db.Column(db.Integer, db.ForeignKey('barbero.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Permite NULL para cliente general
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicio.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Cambiado a user.id en lugar de admin.id
    fecha_hora = db.Column(db.DateTime, nullable=False)
    estado = db.Column(db.String(50), default='pendiente')
    notas = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    barbero = db.relationship('Barbero', back_populates='citas')
    cliente = db.relationship('User', foreign_keys=[cliente_id], back_populates='citas_como_cliente')
    servicio = db.relationship('Servicio', back_populates='citas')
    administrador = db.relationship('User', foreign_keys=[admin_id])  # Relación con User en lugar de Admin
    def __repr__(self):
        return f"<Cita {self.id} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')} - {self.estado}>"



class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    costo = db.Column(db.Float, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=0)
    categoria = db.Column(db.String(50))
    imagen = db.Column(db.String(200))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Add this line

    ventas = db.relationship('SaleDetail', 
                           back_populates='producto',
                           lazy=True)

    def __repr__(self):
        return f"<Producto {self.nombre} - ${self.precio}>"

    def reducir_stock(self, cantidad_vendida):
        if self.cantidad >= cantidad_vendida:
            self.cantidad -= cantidad_vendida
            self.fecha_actualizacion = datetime.utcnow()  # Update timestamp
            db.session.commit()
        else:
            raise ValueError("Stock insuficiente")


class Servicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    duracion = db.Column(db.Integer, nullable=False)  # en minutos
    precio = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True, nullable=False)  # Campo nuevo
    citas = db.relationship('Cita', back_populates='servicio')
     
     
     
class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.now)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    metodo_pago = db.Column(db.String(50), nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    iva = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    descuento = db.Column(db.Float, default=0)
    estado = db.Column(db.String(20), default='completada')
    origen = db.Column(db.String(20), default='presencial')
    
    # Relaciones
    seller = db.relationship('User', foreign_keys=[seller_id])
    cliente = db.relationship('User', foreign_keys=[cliente_id])
    detalles = db.relationship('SaleDetail', back_populates='venta', lazy=True)
    
    def __repr__(self):
        return f"<Sale {self.id} - ${self.total}>"

    @property
    def fecha_formateada(self):
        return self.fecha.strftime('%d/%m/%Y %H:%M')
    
    def calcular_totales(self):
        self.subtotal = sum(detalle.subtotal for detalle in self.detalles)
        self.iva = self.subtotal * 0.16
        self.total = self.subtotal + self.iva - self.descuento

class SaleDetail(db.Model):
    __tablename__ = 'sale_details'
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    descuento_item = db.Column(db.Float, default=0)
    
    # Relaciones
    venta = db.relationship('Sale', back_populates='detalles')
    producto = db.relationship('Producto', back_populates='ventas')

    def __repr__(self):
        return f"<SaleDetail {self.id} - {self.cantidad} x {self.precio_unitario}>"

    def calcular_subtotal(self):
        self.subtotal = self.cantidad * self.precio_unitario - self.descuento_item


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