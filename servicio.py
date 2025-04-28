from app import create_app, db
from app.models import Servicio
from datetime import datetime

def cargar_servicios():
    app = create_app()
    with app.app_context():
        # Lista de servicios a cargar
        servicios_base = [
            {"nombre": "Corte completo", "duracion": 30, "precio": 150.00, "descripcion": "Corte de cabello completo con terminaciones"},
            {"nombre": "Corte barba", "duracion": 20, "precio": 80.00, "descripcion": "Arreglo completo de barba"},
            {"nombre": "Corte ceja", "duracion": 15, "precio": 50.00, "descripcion": "Diseño y arreglo de cejas"},
            {"nombre": "Afeitado clásico", "duracion": 25, "precio": 100.00, "descripcion": "Afeitado con navaja tradicional"},
            {"nombre": "Tinte de cabello", "duracion": 60, "precio": 200.00, "descripcion": "Aplicación de tinte profesional"},
            {"nombre": "Mascarilla capilar", "duracion": 40, "precio": 120.00, "descripcion": "Tratamiento revitalizante"},
            {"nombre": "Corte infantil", "duracion": 25, "precio": 100.00, "descripcion": "Corte especial para niños"}
        ]

        try:
            # Verificar si ya existen servicios
            if Servicio.query.count() > 0:
                print("Ya existen servicios en la base de datos.")
                return

            # Crear y guardar cada servicio
            for servicio_data in servicios_base:
                servicio = Servicio(
                    nombre=servicio_data['nombre'],
                    duracion=servicio_data['duracion'],
                    precio=servicio_data['precio'],
                    descripcion=servicio_data['descripcion'],
                    activo=True
                )
                db.session.add(servicio)

            db.session.commit()
            print(f"Se cargaron {len(servicios_base)} servicios exitosamente!")

        except Exception as e:
            db.session.rollback()
            print(f"Error al cargar servicios: {str(e)}")

if __name__ == '__main__':
    cargar_servicios()