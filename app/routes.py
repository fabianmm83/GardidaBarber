
from flask import render_template, redirect, Blueprint, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import User, Cita, Producto, Venta, Barbero  # Asegúrate de importar todos los modelos necesarios
from app.forms import CitaForm, ProductoForm, AgendarCitaForm
from datetime import datetime
from app.forms import AgendarCitaForm

main_routes = Blueprint('main_routes', __name__)




# Ruta principal
@main_routes.route('/')
def home():
    return render_template('index.html')





# Ruta del dashboard
@main_routes.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'barbero':
        citas = Cita.query.filter_by(barbero_id=current_user.id).all()
    else:
        citas = Cita.query.filter_by(cliente_id=current_user.id).all()
    return render_template('dashboard.html', citas=citas)









@main_routes.route('/agendar_cita', methods=['GET', 'POST'])
@login_required
def agendar_cita():
    if current_user.role != 'cliente':  # Solo los clientes pueden agendar citas
        return redirect(url_for('home'))  # Redirigir si el usuario no es un cliente

    form = AgendarCitaForm()  # Crear el formulario AgendarCitaForm

    
    # Obtener los barberos disponibles
    barberos = User.query.filter_by(role='barbero').all()

    
    # Llenar el SelectField con los barberos
    form.barbero.choices = [(barbero.id, barbero.username) for barbero in barberos]


    if request.method == 'POST' and form.validate_on_submit():
        barbero_id = form.barbero.data  # Obtener el barbero seleccionado
        fecha_hora = form.fecha_hora.data  # Obtener la fecha y hora seleccionada

        # Crear la cita
        cita = Cita(barbero_id=barbero_id, cliente_id=current_user.id, fecha_hora=fecha_hora)
        db.session.add(cita)
        db.session.commit()

        return redirect(url_for('main_routes.mis_citas_cliente'))  # Redirigir a la vista de citas del cliente

    # Pasar el formulario y los barberos a la plantilla
    return render_template('agendar_cita.html', form=form, barberos=barberos)








# Ruta para ver las citas del cliente
@main_routes.route('/mis_citas_cliente', methods=['GET'])
@login_required
def mis_citas_cliente():
    if current_user.role != 'cliente':
        flash("Acceso no autorizado.", 'danger')
        return redirect(url_for('main_routes.dashboard'))  # Redirigir si no es un cliente

    citas = Cita.query.filter_by(cliente_id=current_user.id).all()  # Citas agendadas por el cliente actual
    return render_template('mis_citas_cliente.html', citas=citas)











# Ruta para ver las citas del barbero
@main_routes.route('/mis_citas', methods=['GET'])
@login_required
def mis_citas_barbero():
    if current_user.role != 'barbero':
        flash("Acceso no autorizado.", 'danger')
        return redirect(url_for('main_routes.dashboard'))  # Redirigir si no es un barbero

    citas = Cita.query.filter_by(barbero_id=current_user.id).all()  # Citas asignadas al barbero actual
    return render_template('mis_citas_barbero.html', citas=citas)










# Ruta para cancelar una cita
@main_routes.route('/cancelar_cita/<int:cita_id>', methods=['GET', 'POST'])
@login_required
def cancelar_cita(cita_id):
    cita = Cita.query.get_or_404(cita_id)

    # Verificar si el usuario es el cliente o el barbero que tiene la cita
    if cita.cliente_id != current_user.id and cita.barbero_id != current_user.id:
        flash("No tienes permiso para cancelar esta cita.", 'danger')
        return redirect(url_for('main_routes.dashboard'))

    # Eliminar la cita
    db.session.delete(cita)
    db.session.commit()

    flash("Cita cancelada correctamente.", 'success')
    return redirect(url_for('main_routes.mis_citas_cliente') if current_user.role == 'cliente' else url_for('main_routes.mis_citas_barbero'))









# Ruta para marcar cita como completada
@main_routes.route('/marcar_completada/<int:cita_id>', methods=['GET'])
@login_required
def marcar_completada(cita_id):
    cita = Cita.query.get_or_404(cita_id)

    # Verificar que el barbero sea quien
    # Lógica para marcar cita como completada
    cita.estado = 'completada'  # Asumiendo que tienes un campo 'estado' en la cita
    db.session.commit()

    flash('Cita marcada como completada', 'success')
    return redirect(url_for('main_routes.mis_citas_barbero'))














# Ruta para registrar una venta
@main_routes.route('/ventas', methods=['GET', 'POST'])
@login_required
def ventas():
    productos = Producto.query.all()  # Obtener todos los productos disponibles

    if request.method == 'POST':
        producto_id = request.form['producto_id']
        cantidad = int(request.form['cantidad'])

        producto = Producto.query.get(producto_id)
        if producto and producto.cantidad >= cantidad:  # Verificar que haya suficiente stock
            producto.cantidad -= cantidad  # Reducir la cantidad del producto en inventario
            
            # Registrar la venta en la tabla Venta
            nueva_venta = Venta(
                cliente_id=current_user.id,  # Asumiendo que el cliente es el usuario logueado
                producto_id=producto_id,
                cantidad=cantidad,
                fecha_venta=datetime.utcnow()  # Fecha y hora de la venta
            )
            db.session.add(nueva_venta)  # Agregar la venta a la base de datos
            db.session.commit()  # Confirmar los cambios en la base de datos

            flash('Venta registrada con éxito!', 'success')
            return redirect(url_for('main_routes.ventas'))  # Cambiado a 'main_routes.ventas'

        flash('No hay suficiente stock para realizar esta venta', 'danger')

    return render_template('ventas.html', productos=productos)







## MANEJO DE PRODUCTOS 


# Ruta para ver el inventario (solo barberos)
@main_routes.route('/inventario')
@login_required
def inventario():
    if not current_user.is_authenticated or not current_user.is_barbero:
        flash("No tienes permiso para ver esto", "danger")
        return redirect(url_for('main_routes.dashboard'))
    
    productos = Producto.query.all()
    return render_template('inventario.html', productos=productos)

# Ruta para agregar un producto (solo barberos)
@main_routes.route('/inventario/agregar', methods=['GET', 'POST'])
@login_required
def agregar_producto():
    if not current_user.is_authenticated or not current_user.is_barbero:
        flash("No tienes permiso para hacer esto", "danger")
        return redirect(url_for('main_routes.inventario'))

    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        cantidad = request.form['cantidad']
        precio = request.form['precio']

        nuevo_producto = Producto(
            nombre=nombre,
            descripcion=descripcion,
            cantidad=int(cantidad),
            precio=float(precio)
        )
        db.session.add(nuevo_producto)
        db.session.commit()

        flash("Producto agregado exitosamente", "success")
        return redirect(url_for('main_routes.inventario'))
    
    return render_template('agregar_producto.html')

# Ruta para editar un producto
@main_routes.route('/inventario/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    if not current_user.is_authenticated or not current_user.is_barbero:
        flash("No tienes permiso para hacer esto", "danger")
        return redirect(url_for('main_routes.inventario'))

    producto = Producto.query.get_or_404(id)

    if request.method == 'POST':
        producto.nombre = request.form['nombre']
        producto.descripcion = request.form['descripcion']
        producto.cantidad = int(request.form['cantidad'])
        producto.precio = float(request.form['precio'])

        db.session.commit()
        flash("Producto actualizado correctamente", "success")
        return redirect(url_for('main_routes.inventario'))

    return render_template('editar_producto.html', producto=producto)

# Ruta para eliminar un producto
@main_routes.route('/inventario/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_producto(id):
    if not current_user.is_authenticated or not current_user.is_barbero:
        flash("No tienes permiso para hacer esto", "danger")
        return redirect(url_for('main_routes.inventario'))

    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    flash("Producto eliminado", "success")

    return redirect(url_for('main_routes.inventario'))