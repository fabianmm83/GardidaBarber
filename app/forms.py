from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateTimeField
from wtforms import DateTimeField
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, HiddenField
from wtforms.validators import DataRequired, Email, DataRequired, Email, Length, Regexp
from wtforms.validators import DataRequired, EqualTo
from wtforms import IntegerField, DecimalField


class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')
    
    
    
    

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




class CitaForm(FlaskForm):
    barbero_id = SelectField('Barbero', coerce=int, validators=[DataRequired()])
    fecha_hora = DateTimeField('Fecha y Hora', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    submit = SubmitField('Agendar Cita')

class ProductoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    descripcion = StringField('Descripción')
    precio = FloatField('Precio', validators=[DataRequired()])
    cantidad = IntegerField('Cantidad', validators=[DataRequired()])
    submit = SubmitField('Guardar Producto')


class AgendarCitaForm(FlaskForm):
    barbero = SelectField('Barbero', coerce=int, validators=[DataRequired()])
    fecha_hora = DateTimeField('Fecha y Hora', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    



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