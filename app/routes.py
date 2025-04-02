from flask import render_template, redirect, Blueprint, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import User, Cita, Producto, Venta, Barbero, EditarUsuarioForm
from app.forms import CitaForm, ProductoForm, AgendarCitaForm, BarberoForm
from datetime import datetime
from functools import wraps

main_routes = Blueprint('main_routes', __name__)





def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return role_required('admin')(f)

def barbero_required(f):
    return role_required('barbero', 'admin')(f)

def cliente_required(f):
    return role_required('cliente')(f)

@main_routes.route('/')
def home():
    return render_template('shared/index.html')




@main_routes.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'barbero':
        citas = Cita.query.filter_by(barbero_id=current_user.id).all()
    else:
        citas = Cita.query.filter_by(cliente_id=current_user.id).all()
    return render_template('shared/dashboard.html', citas=citas)






@main_routes.route('/agendar_cita', methods=['GET', 'POST'])
@login_required
@cliente_required
def agendar_cita():
    form = AgendarCitaForm()
    barberos = User.query.filter_by(role='barbero').all()
    form.barbero.choices = [(barbero.id, barbero.username) for barbero in barberos]

    if request.method == 'POST' and form.validate_on_submit():
        cita = Cita(
            barbero_id=form.barbero.data,
            cliente_id=current_user.id,
            fecha_hora=form.fecha_hora.data,
            estado='pendiente'
        )
        db.session.add(cita)
        db.session.commit()
        flash('Cita agendada correctamente!', 'success')
        return redirect(url_for('main_routes.mis_citas_cliente'))
        
    return render_template('cliente/agendar.html', form=form, barberos=barberos)







@main_routes.route('/mis_citas_cliente', methods=['GET'])
@login_required
@cliente_required
def mis_citas_cliente():
    citas = Cita.query.filter_by(cliente_id=current_user.id).order_by(Cita.fecha_hora).all()
    return render_template('cliente/citas.html', citas=citas)










@main_routes.route('/mis_citas', methods=['GET'])
@login_required
@barbero_required
def mis_citas_barbero():
    citas = Cita.query.filter_by(barbero_id=current_user.id).order_by(Cita.fecha_hora).all()
    return render_template('barbero/citas.html', citas=citas, User=User)








@main_routes.route('/cancelar_cita/<int:cita_id>', methods=['POST'])
@login_required
def cancelar_cita(cita_id):
    cita = Cita.query.get_or_404(cita_id)
    if cita.cliente_id != current_user.id and cita.barbero_id != current_user.id:
        abort(403)
    
    db.session.delete(cita)
    db.session.commit()
    flash('Cita cancelada correctamente', 'success')
    return redirect(url_for('main_routes.mis_citas_cliente') if current_user.role == 'cliente' else url_for('main_routes.mis_citas_barbero'))









@main_routes.route('/marcar_completada/<int:cita_id>', methods=['POST'])
@login_required
@barbero_required
def marcar_completada(cita_id):
    cita = Cita.query.get_or_404(cita_id)
    cita.estado = 'completada'
    db.session.commit()
    flash('Cita marcada como completada', 'success')
    return redirect(url_for('main_routes.mis_citas_barbero'))











@main_routes.route('/ventas', methods=['GET', 'POST'])
@login_required
def ventas():
    productos = Producto.query.filter(Producto.cantidad > 0).all()
    
    if request.method == 'POST':
        producto_id = request.form.get('producto_id')
        cantidad = int(request.form.get('cantidad', 1))
        
        producto = Producto.query.get(producto_id)
        if producto and producto.cantidad >= cantidad:
            producto.cantidad -= cantidad
            venta = Venta(
                cliente_id=current_user.id,
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=producto.precio,
                total=producto.precio * cantidad,
                fecha_venta=datetime.utcnow()
            )
            db.session.add(venta)
            db.session.commit()
            flash('Venta registrada exitosamente!', 'success')
            return redirect(url_for('main_routes.ventas'))
        flash('No hay suficiente stock', 'danger')
    
    return render_template('shared/ventas.html', productos=productos)




@main_routes.route('/registro_ventas')
@login_required
@admin_required
def registro_ventas():
    page = request.args.get('page', 1, type=int)
    ventas = Venta.query.order_by(Venta.fecha_venta.desc()).paginate(page=page, per_page=10)
    return render_template('admin/registro_ventas.html', ventas=ventas)






@main_routes.route('/agregar_producto', methods=['GET', 'POST'])
@login_required
@admin_required
def agregar_producto():
    form = ProductoForm()
    
    if form.validate_on_submit():
        producto = Producto(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,  # Asegúrate de que coincida con el modelo
            precio=form.precio.data,
            cantidad=form.cantidad.data
        )
        db.session.add(producto)
        db.session.commit()
        flash('Producto agregado correctamente!', 'success')
        return redirect(url_for('main_routes.inventario'))
    
    return render_template('admin/agregar_producto.html', form=form)





@main_routes.route('/editar_producto/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    producto = Producto.query.get_or_404(id)
    
    form = ProductoForm(obj=producto)
    
    if form.validate_on_submit():
        producto.nombre = form.nombre.data
        producto.descripcion = form.descripcion.data
        producto.precio = form.precio.data
        producto.cantidad = form.cantidad.data
        db.session.commit()
        flash('Producto actualizado correctamente!', 'success')
        return redirect(url_for('main_routes.inventario'))

    return render_template('admin/editar_producto.html', form=form, producto=producto)








@main_routes.route('/eliminar_producto/<int:id>', methods=['POST'])
def eliminar_producto(id):
    producto = Producto.query.get(id)  # Buscar el producto por su ID
    if producto:
        try:
            db.session.delete(producto)  # Eliminar el producto de la base de datos
            db.session.commit()  # Confirmar los cambios
            flash('Producto eliminado con éxito', 'success')  # Mensaje de éxito
        except Exception as e:
            db.session.rollback()  # Si ocurre un error, deshacer los cambios
            flash('Hubo un error al eliminar el producto', 'danger')  # Mensaje de error
    else:
        flash('Producto no encontrado', 'danger')  # Mensaje si el producto no existe

    return redirect(url_for('main_routes.inventario'))  # Redirigir al inventario después de la eliminación








@main_routes.route('/inventario')
@login_required
@barbero_required
def inventario():
    productos = Producto.query.all()
    return render_template('admin/inventario.html', productos=productos)













@main_routes.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    citas_hoy = Cita.query.filter(
        Cita.fecha_hora >= datetime.today().date()
    ).count()
    
    total_productos = Producto.query.count()
    total_usuarios = User.query.count()
    
    return render_template('admin/dashboard.html',
                         citas_hoy=citas_hoy,
                         total_productos=total_productos,
                         total_usuarios=total_usuarios)




@main_routes.route('/registrar_barbero', methods=['GET', 'POST'])
@login_required
@admin_required
def registrar_barbero():
    form = BarberoForm()
    
    if form.validate_on_submit():
        try:
            # Generar username automático
            username = f"{form.nombre.data.lower()}.{form.apellido.data.lower()}"
            
            # Crear usuario
            user = User(
                username=username,
                email=form.correo.data,
                role='barbero',
                activo=True
            )
            user.set_password(form.password.data)  # Hashear la contraseña proporcionada
            
            db.session.add(user)
            db.session.commit()
            
            # Crear perfil de barbero
            barbero = Barbero(
                user_id=user.id,
                nombre=form.nombre.data,
                apellido=form.apellido.data,
                telefono=form.telefono.data,
                correo=form.correo.data
            )
            db.session.add(barbero)
            db.session.commit()
            
            flash('Barbero registrado exitosamente!', 'success')
            return redirect(url_for('main_routes.gestion_usuarios'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar barbero: {str(e)}', 'danger')
    
    return render_template('admin/registrar_barbero.html', form=form)





@main_routes.route('/gestion_usuarios')
@login_required
@admin_required

@login_required
def gestion_usuarios():
    if current_user.role != 'admin':
        return redirect(url_for('unauthorized'))  # Si no es admin, redirige
    barberos = User.query.filter_by(role='barbero').all()
    clientes = User.query.filter_by(role='cliente').all()
    return render_template('admin/usuarios.html', barberos=barberos, clientes=clientes)







@main_routes.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
@login_required  # Asegúrate de que el usuario esté logueado
def editar_usuario(id):
    # Obtener el usuario por ID
    usuario = User.query.get(id)  # Aquí 'User' es tu modelo de usuario

    # Si el usuario no existe, redirigir al listado de usuarios
    if usuario is None:
        return redirect(url_for('main_routes.gestion_usuarios'))

    # Crear el formulario y prellenar los campos con los datos del usuario
    form = EditarUsuarioForm(obj=usuario)  # Asegúrate de que 'EditarUsuarioForm' esté bien definido

    # Procesar el formulario
    if form.validate_on_submit():
        usuario.username = form.username.data
        usuario.email = form.email.data
        usuario.role = form.role.data
        usuario.activo = form.activo.data

        # Guardar los cambios en la base de datos
        db.session.commit()

        # Redirigir al listado de usuarios después de la actualización
        return redirect(url_for('main_routes.gestion_usuarios'))

    # Mostrar el formulario de edición
    return render_template('admin/editar_usuario.html', form=form, usuario=usuario)








@main_routes.route('/ver_citas_admin')
@login_required
@admin_required
def ver_citas_admin():
    # Lógica para ver las citas del administrador

    
    return render_template('admin/ver_citas_admin.html')









@main_routes.errorhandler(403)
def forbidden(e):
    flash('No tienes permiso para acceder a esta página', 'danger')
    return redirect(url_for('main_routes.dashboard')), 403


