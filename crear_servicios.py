from app import create_app, db
from app.models import Servicio

def crear_servicios_iniciales():
    app = create_app()
    with app.app_context():
        # Verificar si ya existen servicios
        if Servicio.query.first():
            print("Ya existen servicios en la base de datos")
            return

        # Lista de servicios básicos
        servicios = [
            {
                'nombre': 'Corte completo',
                'descripcion': 'Corte de cabello completo',
                'precio': 25.00,
                'duracion': 30,
                'activo': True
            },
            {
                'nombre': 'Corte barba',
                'descripcion': 'Arreglo y perfilado de barba',
                'precio': 15.00,
                'duracion': 20,
                'activo': True
            },
            {
                'nombre': 'Corte ceja',
                'descripcion': 'Perfilado de cejas',
                'precio': 10.00,
                'duracion': 15,
                'activo': True
            }
        ]

        try:
            for servicio_data in servicios:
                servicio = Servicio(**servicio_data)
                db.session.add(servicio)
            
            db.session.commit()
            print("Servicios creados exitosamente:")
            for servicio in Servicio.query.all():
                print(f"ID: {servicio.id}, Nombre: {servicio.nombre}")
                
        except Exception as e:
            db.session.rollback()
            print(f"Error al crear servicios: {str(e)}")

if __name__ == '__main__':
    crear_servicios_iniciales()