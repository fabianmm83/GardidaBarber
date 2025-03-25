from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config  # Importa la configuración desde config.py

# Instancia de db y otras extensiones
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  # Usa la configuración desde Config

    # Inicializa db, login_manager y migrate con la aplicación
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Importa blueprints después de la configuración
    from app.routes import main_routes  # Importa blueprint de routes
    from app.auth import auth_routes  # Si tienes rutas de autenticación, importa el blueprint de auth
    app.register_blueprint(main_routes)  # Registra el blueprint de rutas
    app.register_blueprint(auth_routes)  # Registra el blueprint de autenticación

    # Definir la función user_loader
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User  # Evitar circularidad importando dentro de la función
        return User.query.get(int(user_id))

    return app