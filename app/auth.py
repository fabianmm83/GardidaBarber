from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app import db
from app.models import User
from app.forms import LoginForm, RegisterForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint

auth_routes = Blueprint('auth', __name__)



@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):  # Verificar el hash de la contraseña
            login_user(user)
            flash('Has iniciado sesión correctamente!', 'success')
            return redirect(url_for('main_routes.dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html', form=form)






@auth_routes.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Asegurarse de almacenar la contraseña en forma de hash
        hashed_password = generate_password_hash(form.password.data)  # Encriptar la contraseña
        user = User(
            username=form.username.data,
            password=hashed_password,  # Guardar la contraseña encriptada
            role=form.role.data
        )
        db.session.add(user)
        db.session.commit()
        flash('Registro exitoso! Por favor inicia sesión.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)










@auth_routes.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('main.index'))
