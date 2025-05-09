from unittest import case
from flask import app, render_template, redirect, Blueprint, url_for, flash, request, abort
from flask_login import login_required, current_user, login_user
from app import db
from app.models import Sale, SaleDetail, Servicio, User, Cita, Producto, Barbero, EditarUsuarioForm
from app.forms import CitaForm, ProductoForm, AgendarCitaForm, BarberoForm, NuevaCitaForm, CompletarPerfilForm, SaleForm
from datetime import datetime, time, timedelta
from functools import wraps
from sqlalchemy import func
import random
import string
import json
from flask import jsonify




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



def verificar_disponibilidad(barbero_id, fecha_hora):
    """
    Verifica si el barbero tiene disponibilidad en el horario solicitado.
    """
    # Verificar si existe una cita en el mismo horario
    cita_existente = Cita.query.filter(
        Cita.barbero_id == barbero_id,
        Cita.fecha_hora == fecha_hora,
        Cita.estado != 'cancelada'  # Ignorar citas canceladas
    ).first()
    
    # Verificar horario de trabajo (9:00 - 20:00)
    hora = fecha_hora.time()
    horario_apertura = time(9, 0)
    horario_cierre = time(20, 0)
    
    if hora < horario_apertura or hora > horario_cierre:
        return False
    
    return cita_existente is None



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




@main_routes.route('/admin/cita/registrar', methods=['POST'])
@login_required
@admin_required
def registrar_cita_admin():
    try:
        data = request.get_json()
        
        # Manejar cliente nuevo
        cliente_id = None
        new_client_created = False
        
        if data.get('is_new_client'):
            nombre_completo = data['cliente'].strip().split(' ', 1)
            nombre = nombre_completo[0]
            apellido = nombre_completo[1] if len(nombre_completo) > 1 else ''
            
            # Crear username y email temporal
            username = f"{nombre.lower()}_{random.randint(1000, 9999)}"
            temp_email = f"{username}@temporal.barberia.com"
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    
            nuevo_cliente = User(
                username=username,
                email=temp_email,
                nombre=nombre,
                apellido=apellido,
                role='cliente',
                activo=True
            )
            nuevo_cliente.set_password(temp_password)
            
            try:
                db.session.add(nuevo_cliente)
                db.session.flush()
                cliente_id = nuevo_cliente.id
                new_client_created = True
            except Exception as e:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': f'Error al crear nuevo cliente: {str(e)}'
                }), 400
        else:
            cliente_id = int(data['cliente']) if data['cliente'] != '0' else None

        # Obtener el barbero y verificar
        barbero_user = User.query.get(data['barbero_id'])
        if not barbero_user:
            return jsonify({
                'success': False,
                'message': 'Barbero no encontrado'
            }), 400

        # Crear la cita usando el ID del usuario barbero directamente
        nueva_cita = Cita(
            barbero_id=data['barbero_id'],  # Usar el ID del usuario directamente
            cliente_id=cliente_id,
            servicio_id=data['servicio_id'],
            fecha_hora=datetime.strptime(data['fecha_hora'], '%Y-%m-%d %H:%M:%S'),
            estado='confirmada',
            admin_id=current_user.id,
            notas=data.get('notas', '')
        )
        
        db.session.add(nueva_cita)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cita registrada exitosamente',
            'new_client_created': new_client_created
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error al registrar cita: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error al registrar la cita: {str(e)}'
        }), 500



@main_routes.route('/admin/cita/nueva', methods=['GET', 'POST'])
@login_required
@admin_required
def nueva_cita_admin():
    """Handle both GET and POST requests for new appointments"""
    if request.method == 'GET':
        form = NuevaCitaForm()
        return render_template('admin/nueva_cita.html',
                             form=form,
                             horario_apertura=time(9, 0),
                             horario_cierre=time(20, 0))
    
    # Handle POST request
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['barbero_id', 'cliente_id', 'servicio_id', 'fecha_hora']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'message': 'Faltan campos requeridos'
            }), 400
            
        # Convert fecha_hora string to datetime
        fecha_hora = datetime.strptime(data['fecha_hora'], '%Y-%m-%d %H:%M:%S')
        
        # Verify availability
        if not verificar_disponibilidad(data['barbero_id'], fecha_hora):
            return jsonify({
                'success': False,
                'message': 'El barbero ya tiene una cita en ese horario'
            }), 400

        # Create new appointment
        nueva_cita = Cita(
            barbero_id=data['barbero_id'],
            cliente_id=data['cliente_id'],
            servicio_id=data['servicio_id'],
            fecha_hora=fecha_hora,
            estado='confirmada',
            admin_id=current_user.id,
            notas=data.get('notas', '')
        )
        
        db.session.add(nueva_cita)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '¡Cita registrada exitosamente!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al registrar la cita: {str(e)}'
        }), 500
        
    
@main_routes.route('/admin/citas')
@login_required
@admin_required
def citas_admin():
    fecha = request.args.get('fecha')
    barbero_id = request.args.get('barbero')
    estado = request.args.get('estado')
    
    query = Cita.query
    
    if fecha:
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        query = query.filter(db.func.date(Cita.fecha_hora) == fecha_obj)  # Usar db.func.date
    
    if barbero_id:
        query = query.filter(Cita.barbero_id == barbero_id)
    
    if estado:
        query = query.filter(Cita.estado == estado)
    
    page = request.args.get('page', 1, type=int)
    citas = query.order_by(Cita.fecha_hora).paginate(page=page, per_page=10)  # Ordenar por fecha_hora
    
    barberos = User.query.filter((User.role == 'barbero') | (User.role == 'admin')).all()
    
    return render_template('admin/citas_admin.html',
                         citas=citas,
                         barberos=barberos,
                         fecha_filtro=fecha,
                         barbero_filtro=barbero_id,
                         estado_filtro=estado,
                         modo='listar')

@main_routes.route('/admin/citas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_cita_admin(id):
    cita = Cita.query.get_or_404(id)
    form = CitaForm(obj=cita)
    
    # Cargar opciones para los select fields
    barberos = User.query.filter((User.role == 'barbero') | (User.role == 'admin')).all()
    form.barbero.choices = [(b.id, b.username) for b in barberos]
    
    clientes = User.query.filter_by(role='cliente').all()
    form.cliente_id.choices = [(0, 'Cliente General')] + [(c.id, c.username) for c in clientes]
    
    servicios = Servicio.query.filter_by(activo=True).all()
    form.servicio.choices = [(s.id, s.nombre) for s in servicios]
    
    if form.validate_on_submit():
        try:
            # Solo actualizar los campos que han sido modificados
            if form.barbero.data:
                cita.barbero_id = form.barbero.data
            if form.cliente_id.data is not None:
                cita.cliente_id = form.cliente_id.data if form.cliente_id.data != 0 else None
            if form.servicio.data:
                cita.servicio_id = form.servicio.data
            if form.fecha_hora.data:
                cita.fecha_hora = form.fecha_hora.data
            if form.notas.data:
                cita.notas = form.notas.data
            if form.estado.data:
                cita.estado = form.estado.data
            
            db.session.commit()
            flash('Cita actualizada correctamente', 'success')
            return redirect(url_for('main_routes.citas_admin'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la cita: {str(e)}', 'danger')
    
    # Si es GET, formatear la fecha para el campo datetime-local
    if request.method == 'GET' and cita.fecha_hora:
        form.fecha_hora.data = cita.fecha_hora
    
    return render_template('admin/editar_cita.html', form=form, cita=cita)


@main_routes.route('/admin/citas/eliminar/<int:id>')
@login_required
@admin_required
def eliminar_cita_admin(id):
    try:
        cita = Cita.query.get_or_404(id)
        
        # Eliminar la cita
        db.session.delete(cita)
        db.session.commit()
        
        flash('Cita eliminada correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la cita: {str(e)}', 'danger')
    
    return redirect(url_for('main_routes.citas_admin'))    
    
    
    

    
@main_routes.route('/admin/citas/cambiar-estado/<int:id>', methods=['POST'])
@login_required
@admin_required
def cambiar_estado_cita(id):
    cita = Cita.query.get_or_404(id)
    nuevo_estado = request.form.get('estado')
    
    if nuevo_estado not in ['pendiente', 'confirmada', 'completada', 'cancelada']:
        flash('Estado no válido', 'danger')
        return redirect(url_for('main_routes.citas_admin'))
    
    estado_anterior = cita.estado
    cita.estado = nuevo_estado
    db.session.commit()
    
    flash(f'Cita cambiada de {estado_anterior} a {nuevo_estado}', 'success')
    return redirect(url_for('main_routes.citas_admin'))




##agendar cita desde cliente
@main_routes.route('/agendar_cita', methods=['GET', 'POST'])
@login_required
@cliente_required
def agendar_cita():
    form = AgendarCitaForm()
    
    # Obtener barberos (incluyendo admins que pueden actuar como barberos)
    barberos = User.query.filter((User.role == 'barbero') | (User.role == 'admin')).all()
    form.barbero.choices = [(barbero.id, f"{barbero.username} ({'Admin' if barbero.role == 'admin' else 'Barbero'})") 
                          for barbero in barberos]

    # Resto del código permanece igual...
    servicios = Servicio.query.filter_by(activo=True).all()
    form.servicio.choices = [(servicio.id, f"{servicio.nombre} - {servicio.duracion} min") 
                           for servicio in servicios]

    if form.validate_on_submit():
        try:
            servicio = Servicio.query.get(form.servicio.data)
            hora_fin = (datetime.strptime(str(form.fecha_hora.data), '%Y-%m-%d %H:%M:%S') + 
                       timedelta(minutes=servicio.duracion)).time()
            
            if not verificar_disponibilidad(form.barbero.data, form.fecha_hora.data.date(), 
                                          form.fecha_hora.data.time(), hora_fin):
                flash('El profesional ya tiene una cita en ese horario', 'danger')
                return redirect(url_for('main_routes.agendar_cita'))

            nueva_cita = Cita(
                barbero_id=form.barbero.data,
                cliente_id=current_user.id,
                servicio_id=form.servicio.data,
                fecha=form.fecha_hora.data.date(),
                hora_inicio=form.fecha_hora.data.time(),
                hora_fin=hora_fin,
                estado='pendiente',
                notas=form.notas.data
            )
            
            db.session.add(nueva_cita)
            db.session.commit()
            
            flash('¡Cita agendada correctamente!', 'success')
            return redirect(url_for('main_routes.mis_citas_cliente'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agendar cita: {str(e)}', 'danger')

    return render_template('cliente/agendar.html', 
                         form=form, 
                         barberos=barberos,
                         servicios=servicios,
                         horario_apertura=time(9, 0),
                         horario_cierre=time(20, 0))






##cliente citas
@main_routes.route('/mis_citas_cliente', methods=['GET'])
@login_required
@cliente_required
def mis_citas_cliente():
    citas = Cita.query.filter_by(cliente_id=current_user.id).order_by(Cita.fecha_hora).all()
    return render_template('cliente/citas.html', citas=citas)








##citas vista desde barbero
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



@main_routes.route('/ventas', methods=['GET'])
@login_required
@role_required('admin', 'barbero')
def ventas():
    # Obtener parámetros de filtro
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    metodo_pago = request.args.get('metodo_pago')
    seller_id = request.args.get('seller_id')
    
    # Query base
    query = Sale.query
    
    # Aplicar filtros
    if fecha_inicio and fecha_fin:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(Sale.fecha.between(fecha_inicio, fecha_fin))
    if metodo_pago:
        query = query.filter(Sale.metodo_pago == metodo_pago)
    if seller_id:
        query = query.filter(Sale.seller_id == seller_id)
    
    # Ordenar y paginar
    ventas = query.order_by(Sale.fecha.desc()).paginate(
        page=request.args.get('page', 1, type=int),
        per_page=10
    )
    
    # Obtener totales
    totales = {
        'subtotal': sum(v.subtotal for v in ventas.items),
        'iva': sum(v.iva for v in ventas.items),
        'descuento': sum(v.descuento for v in ventas.items),
        'total': sum(v.total for v in ventas.items)
    }
    
    return render_template('ventas/ventas.html', 
                         ventas=ventas,
                         totales=totales,
                         fecha_inicio=fecha_inicio,
                         fecha_fin=fecha_fin,
                         metodo_pago=metodo_pago)






@main_routes.route('/registrar-venta', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'barbero')
def registrar_venta():
    form = SaleForm()
    
    # Configurar las opciones del select de clientes
    form.cliente_id.choices = [(0, 'Cliente ocasional')] + [
        (u.id, f"{u.username} ({u.email})") 
        for u in User.query.filter_by(role='cliente').all()
    ]
    
    # Obtener productos disponibles con paginación
    productos_disponibles = Producto.query.filter(
        Producto.cantidad > 0
    ).paginate(
        page=request.args.get('page', 1, type=int),
        per_page=9
    )
    
    if request.method == 'POST':
        if request.is_json:
            try:
                data = request.get_json()
                
                nueva_venta = Sale(
                    seller_id=current_user.id,
                    cliente_id=data.get('cliente_id'),
                    metodo_pago=data.get('metodo_pago'),
                    subtotal=float(data.get('subtotal')),
                    iva=float(data.get('iva')),
                    total=float(data.get('total')),
                    descuento=float(data.get('descuento', 0)),
                    estado='completada',
                    origen='presencial',
                    fecha=datetime.now() 
                )
                
                db.session.add(nueva_venta)
                db.session.flush()
                
                # Procesar detalles de venta
                for item in data.get('productos', []):
                    producto = Producto.query.get(item['id'])
                    if not producto or producto.cantidad < item['cantidad']:
                        raise ValueError(f'Stock insuficiente para {producto.nombre if producto else "producto"}')
                    
                    detalle = SaleDetail(
                        venta_id=nueva_venta.id,
                        producto_id=producto.id,
                        cantidad=item['cantidad'],
                        precio_unitario=item['precio'],
                        subtotal=item['subtotal']
                    )
                    
                    db.session.add(detalle)
                    producto.cantidad -= item['cantidad']
                
                db.session.commit()
                return jsonify({'success': True, 'message': 'Venta registrada exitosamente'})
                
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': str(e)}), 400
    
    return render_template('ventas/registrar_venta.html', 
                         form=form,
                         productos_disponibles=productos_disponibles)


@main_routes.route('/ventas/eliminar/<int:venta_id>', methods=['POST'])
@login_required
def eliminar_venta(venta_id):
    try:
        venta = Sale.query.get_or_404(venta_id)
        
        # First restore product stock
        for detalle in venta.detalles:
            producto = detalle.producto
            if producto:
                producto.cantidad += detalle.cantidad
        
        # Delete all sale details first
        SaleDetail.query.filter_by(venta_id=venta_id).delete()
        
        # Then delete the sale
        db.session.delete(venta)
        db.session.commit()
        
        flash('Venta eliminada correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la venta: {str(e)}', 'danger')
    
    return redirect(url_for('main_routes.ventas'))

##CREAR 
@main_routes.route('/agregar_producto', methods=['GET', 'POST'])
@login_required
@admin_required
def agregar_producto():
    form = ProductoForm()
    
    if form.validate_on_submit():
        try:
            # Crear el producto con todos los campos requeridos
            producto = Producto(
                nombre=form.nombre.data.strip(),  # strip() elimina espacios en blanco
                descripcion=form.descripcion.data.strip() if form.descripcion.data else None,
                costo=float(form.costo.data),  # Conversión explícita a float
                precio=float(form.precio.data),
                cantidad=int(form.cantidad.data),
                categoria=form.categoria.data.strip() if form.categoria.data else None,
                # imagen se manejaría por separado si tienes uploads de archivos
            )
            
            db.session.add(producto)
            db.session.commit()
            flash('Producto agregado correctamente!', 'success')
            return redirect(url_for('main_routes.inventario'))
            
        except ValueError as e:
            db.session.rollback()
            flash(f'Error en los datos numéricos: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar el producto: {str(e)}', 'danger')
    
    return render_template('admin/agregar_producto.html', form=form)

##UPDATE
@main_routes.route('/editar_producto/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    producto = Producto.query.get_or_404(id)
    form = ProductoForm(obj=producto)
    
    if form.validate_on_submit():
        form.populate_obj(producto)  # Actualiza todos los campos automáticamente
        db.session.commit()
        flash('Producto actualizado correctamente!', 'success')
        return redirect(url_for('main_routes.inventario'))

    return render_template('admin/editar_producto.html', form=form, producto=producto)

##DELETE
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



#VER INVENTARIO
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
    # Estadísticas básicas
    total_clientes = User.query.filter_by(role='cliente').count()
    total_productos = Producto.query.count()
    citas_hoy = Cita.query.filter(Cita.fecha_hora >= datetime.today()).count()
    
    # Estadísticas adicionales
    nuevos_clientes_mes = User.query.filter(
        User.role == 'cliente',
        User.fecha_registro >= datetime.today().replace(day=1)
    ).count()
    
    # Ventas
    ventas_hoy = Sale.query.filter(
        Sale.fecha >= datetime.today()
    ).with_entities(func.sum(Sale.total)).scalar() or 0
    
    # Últimas ventas
    ultimas_ventas = Sale.query.order_by(Sale.fecha.desc()).limit(5).all()
    
    # Próximas citas
    proximas_citas = Cita.query.filter(
        Cita.fecha_hora >= datetime.now()
    ).order_by(Cita.fecha_hora).limit(5).all()
    
    return render_template('admin/dashboard.html',
        total_clientes=total_clientes,
        total_productos=total_productos,
        citas_hoy=citas_hoy,
        nuevos_clientes_mes=nuevos_clientes_mes,
        ventas_hoy=ventas_hoy,
        ultimas_ventas=ultimas_ventas,
        proximas_citas=proximas_citas,
        productos_bajos_stock=Producto.query.filter(Producto.cantidad < 5).count(),
        porcentaje_ventas="+15",  # Esto deberías calcularlo comparando con el día anterior
        User=User  # Agregar el modelo User al contexto del template
    )


##desde admin
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




##desde admin
@main_routes.route('/reportes')
@login_required
@admin_required
def ver_reportes():
    # Obtener parámetros de filtro
    fecha_inicio = request.args.get('fecha_inicio', datetime.now().replace(day=1).strftime('%Y-%m-%d'))
    fecha_fin = request.args.get('fecha_fin', datetime.now().strftime('%Y-%m-%d'))
    barbero_id = request.args.get('barbero_id')
    tipo = request.args.get('tipo')

    # Convertir fechas
    fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')

    # Obtener estadísticas de barberos
    estadisticas_barberos = db.session.query(
        User,
        db.func.count(Cita.id).label('total_citas'),
        db.func.count(db.case([(Cita.estado == 'completada', 1)])).label('citas_completadas'),
        db.func.count(db.case([(Cita.estado == 'pendiente', 1)])).label('citas_pendientes')
    ).outerjoin(Cita, User.id == Cita.barbero_id)\
    .filter(User.role.in_(['barbero', 'admin']))\
    .filter(Cita.fecha_hora.between(fecha_inicio, fecha_fin) if barbero_id else True)\
    .group_by(User.id)\
    .order_by(db.func.count(Cita.id).desc())\
    .all()

    # Análisis de clientes
    total_clientes = User.query.filter_by(role='cliente').count()
    clientes_nuevos = User.query.filter(
        User.role == 'cliente',
        User.fecha_registro >= datetime.now() - timedelta(days=30)
    ).count()

    # Análisis de citas
    query_citas = Cita.query.filter(Cita.fecha_hora.between(fecha_inicio, fecha_fin))
    if barbero_id:
        query_citas = query_citas.filter_by(barbero_id=barbero_id)

    total_citas = query_citas.count()
    citas_pendientes = query_citas.filter_by(estado='pendiente').count()
    citas_completadas = query_citas.filter_by(estado='completada').count()

    # Análisis de inventario
    productos = Producto.query.all()
    total_productos = len(productos)
    cantidad_total = sum(p.cantidad for p in productos)
    inversion_total = sum(p.cantidad * p.costo for p in productos)
    valor_inventario = sum(p.cantidad * p.precio for p in productos)

    # Ventas por período
    ventas = Sale.query.filter(Sale.fecha.between(fecha_inicio, fecha_fin))
    total_ventas = ventas.with_entities(db.func.sum(Sale.total)).scalar() or 0

    # Producto más vendido en el período
    producto_mas_vendido = db.session.query(
        Producto.nombre,
        db.func.sum(SaleDetail.cantidad).label('total_vendido')
    ).join(SaleDetail)\
    .join(Sale)\
    .filter(Sale.fecha.between(fecha_inicio, fecha_fin))\
    .group_by(Producto.id, Producto.nombre)\
    .order_by(db.func.sum(SaleDetail.cantidad).desc())\
    .first()

    # Barbero con más citas en el período
    barbero_mas_citas = db.session.query(
        User.username,
        db.func.count(Cita.id).label('total_citas')
    ).join(Cita, User.id == Cita.barbero_id)\
    .filter(User.role == 'barbero')\
    .filter(Cita.fecha_hora.between(fecha_inicio, fecha_fin))\
    .group_by(User.id, User.username)\
    .order_by(db.func.count(Cita.id).desc())\
    .first()

    # Cálculo de ingresos y gastos
    # Ingresos por ventas
    ventas_periodo = Sale.query.filter(Sale.fecha.between(fecha_inicio, fecha_fin)).all()
    ingresos_ventas = sum(venta.total for venta in ventas_periodo)
    
    # Ingresos por citas completadas
    citas_periodo = Cita.query.filter(
        Cita.fecha_hora.between(fecha_inicio, fecha_fin),
        Cita.estado == 'completada'
    ).all()
    ingresos_citas = len(citas_periodo) * 150  # $150 por cita

    # Gastos por inventario
    productos_periodo = Producto.query.filter(
        Producto.fecha_actualizacion.between(fecha_inicio, fecha_fin)
    ).all()
    gastos_totales = sum(producto.costo * producto.cantidad for producto in productos_periodo)

    # Total de ingresos
    ingresos_totales = ingresos_ventas + ingresos_citas

    # Obtener lista de barberos para el filtro
    barberos = User.query.filter_by(role='barbero').all()

    return render_template('reportes/reportes.html',
        total_clientes=total_clientes,
        clientes_nuevos=clientes_nuevos,
        total_citas=total_citas,
        citas_pendientes=citas_pendientes,
        citas_completadas=citas_completadas,
        total_productos=total_productos,
        cantidad_total=cantidad_total,
        inversion_total=inversion_total,
        valor_inventario=valor_inventario,
        total_ventas=total_ventas,
        producto_mas_vendido=producto_mas_vendido,
        barbero_mas_citas=barbero_mas_citas,
        ingresos_totales=ingresos_totales,
        gastos_totales=gastos_totales,
        ingresos_citas=ingresos_citas,
        ingresos_ventas=ingresos_ventas,
        barberos=barberos,
        fecha_inicio=fecha_inicio.strftime('%Y-%m-%d'),
        fecha_fin=fecha_fin.strftime('%Y-%m-%d'),
        estadisticas_barberos=estadisticas_barberos
    )



##desdea admin
@main_routes.route('/gestion_usuarios')
@login_required
@admin_required
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




@main_routes.errorhandler(403)
def forbidden(e):
    flash('No tienes permiso para acceder a esta página', 'danger')
    return redirect(url_for('main_routes.dashboard')), 403







@main_routes.route('/nueva-cita', methods=['GET', 'POST'])
def nueva_cita():
    """Flujo integrado de primera cita para clientes nuevos"""
    form = NuevaCitaForm()
    
    if form.validate_on_submit():
        # Verificar si ya existe usuario con este teléfono
        phone_user = User.query.filter_by(phone=form.phone.data).first()
        
        if phone_user:
            # Si el usuario existe, iniciar sesión
            login_user(phone_user)
            flash('Ya tienes una cuenta con este teléfono. Sesión iniciada.', 'info')
        else:
            # Crear usuario guest
            # Generar nombre de usuario único basado en el teléfono
            username = f"guest_{form.phone.data.replace('+', '').replace(' ', '')}"
            temp_email = f"{username}@guest.gardidabarber.com"
            
            # Generar contraseña aleatoria
            random_pass = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            
            new_user = User(
                username=username,
                email=temp_email,
                role='cliente',
                is_guest=True,
                phone=form.phone.data,
                activo=True
            )
            new_user.set_password(random_pass)
            
            try:
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                flash('Cuenta temporal creada. Puedes completar tu perfil más tarde.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error al crear usuario: {str(e)}', 'danger')
                return redirect(url_for('main_routes.nueva_cita'))
        
        # Redireccionar a selección de barbero (agendar cita)
        return redirect(url_for('main_routes.agendar_cita'))
    
    return render_template('cliente/nueva_cita.html', form=form)








@main_routes.route('/completar-perfil', methods=['GET', 'POST'])
@login_required
def completar_perfil():
    """Permite que usuarios guest completen su información"""
    # Si no es guest o no es cliente, redirigir
    if not current_user.is_guest or current_user.role != 'cliente':
        return redirect(url_for('main_routes.dashboard'))
        
    form = CompletarPerfilForm()
    
    if form.validate_on_submit():
        try:
            # Verificar si el email ya está en uso
            email_exists = User.query.filter(User.email == form.email.data, 
                                          User.id != current_user.id).first()
            if email_exists:
                flash('Este correo ya está registrado. Usa otro.', 'danger')
                return redirect(url_for('main_routes.completar_perfil'))
            
            # Verificar si el username está en uso (si se proporcionó)
            if form.username.data:
                username_exists = User.query.filter(User.username == form.username.data, 
                                                User.id != current_user.id).first()
                if username_exists:
                    flash('Este nombre de usuario ya está en uso. Elige otro.', 'danger')
                    return redirect(url_for('main_routes.completar_perfil'))
                
                # Actualizar username si se proporcionó uno
                current_user.username = form.username.data
            
            # Actualizar datos de usuario
            current_user.email = form.email.data
            current_user.set_password(form.password.data)
            current_user.is_guest = False
            
            db.session.commit()
            flash('¡Perfil actualizado exitosamente!', 'success')
            return redirect(url_for('main_routes.mis_citas_cliente'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar perfil: {str(e)}', 'danger')
    
    return render_template('cliente/completar_perfil.html', form=form)



@main_routes.route('/api/clientes')
@login_required
def get_clientes():
    try:
        clientes = User.query.filter_by(role='cliente').all()
        return jsonify([{
            'id': c.id,
            'username': c.username,  # Cambiado de 'nombre' a 'username' para coincidir con el JS
            'nombre': getattr(c, 'nombre', c.username),  # Campo adicional por si acaso
            'apellido': getattr(c, 'apellido', '')  # Campo adicional
        } for c in clientes])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_routes.route('/api/barberos')
@login_required
def get_barberos():
    try:
        # Obtener barberos (usuarios con rol barbero)
        barberos = User.query.filter_by(role='barbero').all()
        barberos_list = [{
            'id': b.id,
            'username': b.username,  # Campo principal
            'nombre': getattr(b, 'nombre', b.username),
            'apellido': getattr(b, 'apellido', '')
        } for b in barberos]
        
        # Obtener administradores
        admins = User.query.filter_by(role='admin').all()
        admin_list = [{
            'id': a.id,
            'username': a.username,
            'nombre': a.username,
            'apellido': '(Admin)'
        } for a in admins]
        
        return jsonify(barberos_list + admin_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@main_routes.route('/api/servicios')
@login_required
def get_servicios():
    try:
        # Primero intenta obtener de la base de datos
        servicios_db = Servicio.query.filter_by(activo=True).all()
        
        if servicios_db:
            return jsonify([{
                'id': servicio.id,
                'nombre': servicio.nombre
            } for servicio in servicios_db])
        else:
            # Si no hay servicios en la BD, devuelve los predeterminados
            servicios_default = [
                {'id': 1, 'nombre': 'Corte completo'},
                {'id': 2, 'nombre': 'Corte barba'},
                {'id': 3, 'nombre': 'Corte ceja'}
            ]
            return jsonify(servicios_default)
            
    except Exception as e:
        print(f"Error en API servicios: {str(e)}")
        # Devuelve los servicios predeterminados si hay error
        return jsonify([
            {'id': 1, 'nombre': 'Corte completo'},
            {'id': 2, 'nombre': 'Corte barba'},
            {'id': 3, 'nombre': 'Corte ceja'}
        ])

# Endpoint AJAX para buscar productos
@main_routes.route('/api/productos/buscar', methods=['GET'])
@login_required
def buscar_productos():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
        
    productos = Producto.query.filter(
        Producto.nombre.ilike(f'%{query}%') & 
        (Producto.cantidad > 0)
    ).limit(10).all()
    
    return jsonify([{
        'id': p.id,
        'nombre': p.nombre,
        'precio': p.precio,
        'stock': p.cantidad,
        'imagen': p.imagen or ''
    } for p in productos])
    
    
    
    
    