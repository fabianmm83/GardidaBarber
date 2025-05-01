import os
from dotenv import load_dotenv


import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    
    # Configuración de base de datos
    if os.environ.get('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
        database_type = "PostgreSQL en Render"
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance", "database.db")
        database_type = "SQLite"
    
    @classmethod
    def print_database_info(cls):
        print(f"Conectado a: {cls.database_type}")
        print(f"URI de la base de datos: {cls.SQLALCHEMY_DATABASE_URI}")
    
