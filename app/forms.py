from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateTimeField
from wtforms import DateTimeField

from wtforms.validators import DataRequired, EqualTo
from wtforms import IntegerField, DecimalField


class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')

class RegisterForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Rol', choices=[('barbero', 'Barbero'), ('cliente', 'Cliente')], validators=[DataRequired()])
    submit = SubmitField('Registrarse')

class CitaForm(FlaskForm):
    barbero_id = SelectField('Barbero', coerce=int, validators=[DataRequired()])
    fecha_hora = DateTimeField('Fecha y Hora', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    submit = SubmitField('Agendar Cita')

class ProductoForm(FlaskForm):
    nombre = StringField('Nombre del Producto', validators=[DataRequired()])
    cantidad = IntegerField('Cantidad en Inventario', validators=[DataRequired()])
    precio = DecimalField('Precio', validators=[DataRequired()])
    submit = SubmitField('Guardar Producto')


class AgendarCitaForm(FlaskForm):
    barbero = SelectField('Barbero', coerce=int, validators=[DataRequired()])
    fecha_hora = DateTimeField('Fecha y Hora', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])