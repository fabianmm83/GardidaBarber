from flask import render_template, redirect, url_for, flash, abort, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db, login_manager
from app.models import User
from app.forms import LoginForm, RegistrationForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint
from functools import wraps
from datetime import datetime

auth_routes = Blueprint('auth', __name__)




def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.username.data)
        ).first()
        
        if user and user.check_password(form.password.data):
            if user.activo:
                login_user(user)
                flash(f'Bienvenido {user.username}!', 'success')
                
             # Redirección basada en rol
                if user.role == 'admin':
                    return redirect(url_for('main_routes.admin_dashboard'))
                elif user.role == 'barbero':
                     return redirect(url_for('main_routes.mis_citas_barbero'))
                else:
                    return redirect(url_for('main_routes.mis_citas_cliente'))
            else:
                flash('Tu cuenta está desactivada', 'warning')
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('auth/login.html', form=form)






@auth_routes.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(
                username=form.username.data,
                email=form.email.data,
                role='cliente'
            )
            user.set_password(form.password.data)  # Hashear aquí
            db.session.add(user)
            db.session.commit()
            flash('Registro exitoso!', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Error al registrar: ' + str(e), 'danger')
    return render_template('auth/register.html', form=form)






@auth_routes.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('main_routes.home'))




