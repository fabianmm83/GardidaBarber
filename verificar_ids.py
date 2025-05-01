from app import create_app, db
from app.models import User, Barbero, Cita

def verificar_ids():
    app = create_app()
    with app.app_context():
        # Obtener admin y su perfil de barbero
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            print("No se encontró el admin")
            return
        
        print(f"\nInformación del Admin:")
        print(f"Admin ID: {admin.id}")
        print(f"Username: {admin.username}")
        
        barbero = Barbero.query.filter_by(user_id=admin.id).first()
        if not barbero:
            print("No se encontró el perfil de barbero")
            return
            
        print(f"\nInformación del Barbero:")
        print(f"Barbero ID: {barbero.id}")
        print(f"User ID: {barbero.user_id}")
        
        # Verificar citas existentes
        citas = Cita.query.filter_by(barbero_id=barbero.id).all()
        print(f"\nCitas asociadas al barbero:")
        for cita in citas:
            print(f"Cita ID: {cita.id}, Barbero ID: {cita.barbero_id}")

if __name__ == '__main__':
    verificar_ids()