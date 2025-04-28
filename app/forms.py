
from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, StringField, PasswordField, SubmitField, SelectField, DateTimeField, TimeField
from wtforms import DateTimeField
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, FloatField, HiddenField
from wtforms.validators import DataRequired, Email, DataRequired, Email, Length, Regexp
from wtforms.validators import DataRequired, EqualTo, Optional
from wtforms import IntegerField, DecimalField



class LoginForm(FlaskForm):
    # Mantener campos existentes
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recordarme')
    phone = StringField('O ingresa con tu teléfono', validators=[])
    is_phone_login = HiddenField(default='0')
    submit = SubmitField('Ingresar')
    
    
  
    # Validador personalizado
    def validate(self):
        if not super().validate():
            return False
        # Verificar que haya al menos username+password o teléfono
        if (not self.username.data or not self.password.data) and not self.phone.data:
            self.username.errors.append('Proporciona credenciales o teléfono')
            return False
        return True
    
    
class RegistrationForm(FlaskForm):
    username = StringField('Usuario', validators=[
        DataRequired(),
        Length(min=4, max=25)
    ])
    email = StringField('Correo Electrónico', validators=[
        DataRequired(),
        Email(message='Ingresa un correo electrónico válido')
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(),
        Length(min=6)
    ])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(),
        EqualTo('password', message='Las contraseñas deben coincidir')
    ])
    role = HiddenField(default='cliente')  # Campo oculto que siempre será 'cliente'
    submit = SubmitField('Registrarse')


# Añadir estos formularios en forms.py

class NuevaCitaForm(FlaskForm):
    fecha = DateField('Fecha', validators=[DataRequired()])
    hora = TimeField('Hora', validators=[DataRequired()])
    cliente = SelectField('Cliente', coerce=int)
    servicio = SelectField('Servicio', choices=[
        ('corte', 'Corte de Cabello'),
        ('barba', 'Corte de Barba'),
        ('completo', 'Corte Completo')
    ])
    barbero = SelectField('Barbero', coerce=int)
    submit = SubmitField('Registrar Cita')


class CompletarPerfilForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[
        DataRequired(),
        Email(message='Ingresa un correo electrónico válido')
    ])
    username = StringField('Nombre de Usuario (opcional)', validators=[Length(min=4, max=25)])
    password = PasswordField('Contraseña', validators=[
        DataRequired(),
        Length(min=6, message="La contraseña debe tener al menos 6 caracteres")
    ])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(),
        EqualTo('password', message='Las contraseñas deben coincidir')
    ])
    submit = SubmitField('Completar Perfil')


class CitaForm(FlaskForm):
    barbero_id = SelectField('Barbero', coerce=int, validators=[DataRequired()])
    servicio_id = SelectField('Servicio', coerce=int, validators=[DataRequired()])
    fecha = DateTimeField('Fecha y Hora', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    notas = TextAreaField('Notas Adicionales')
    submit = SubmitField('Agendar Cita')

class ProductoForm(FlaskForm):
    nombre = StringField('Nombre del Producto', validators=[DataRequired()])
    descripcion = TextAreaField('Descripción')  # Cambiado a TextAreaField para más espacio
    costo = FloatField('Costo de Adquisición', validators=[DataRequired()])
    precio = FloatField('Precio de Venta al Público', validators=[DataRequired()])
    cantidad = IntegerField('Cantidad en Stock', validators=[DataRequired()])
    
    # Campo de categoría con opción para escribir libremente
    categoria = SelectField('Categoría', 
        choices=[
            ('', 'Seleccione o escriba una categoría'),
            ('cuidado_cabello', 'Cuidado del Cabello'),
            ('afeitado', 'Productos de Afeitado'),
            ('accesorios', 'Accesorios'),
            ('otros', 'Otros')
        ],
        render_kw={"data-allow-clear": "true", "data-tags": "true"}
    )
    
    submit = SubmitField('Guardar Producto')


class SaleForm(FlaskForm):
    cliente_id = SelectField('Cliente (Opcional)', coerce=int)
    metodo_pago = SelectField('Método de Pago', choices=[
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta de Crédito/Débito'),
        ('transferencia', 'Transferencia'),
        ('qr', 'Pago con QR')
    ], validators=[DataRequired(message="Seleccione un método de pago")])
    productos_json = HiddenField('Productos')
    submit = SubmitField('Finalizar Venta')


class AgendarCitaForm(FlaskForm):
    barbero = SelectField('Barbero', coerce=int, validators=[DataRequired()])
    servicio = SelectField('Servicio', coerce=int, validators=[DataRequired()])
    cliente_id = SelectField('Cliente', coerce=int)
    fecha_hora = DateTimeField('Fecha y Hora', 
                              format='%Y-%m-%d %H:%M',
                              validators=[DataRequired()],
                              render_kw={"autocomplete": "off"})
    notas = TextAreaField('Notas adicionales')
    submit = SubmitField('Agendar Cita')

class BarberoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    apellido = StringField('Apellido', validators=[DataRequired()])
    telefono = StringField('Teléfono', validators=[
        DataRequired(),
        Regexp(r'^\+?\d{8,15}$', message="Formato: +5212345678 o 12345678")
    ])
    correo = StringField('Correo', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña Temporal', validators=[
        DataRequired(),
        Length(min=8, message="La contraseña debe tener al menos 8 caracteres")
    ])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(),
        EqualTo('password', message="Las contraseñas no coinciden")
    ])
    submit = SubmitField('Registrar Barbero')