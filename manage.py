from app import create_app, db
from flask_migrate import Migrate, MigrateCommand
from flask.cli import FlaskGroup

app = create_app()
migrate = Migrate(app, db)

cli = FlaskGroup(app)

# Registra el comando de migración
cli.add_command(MigrateCommand)

if __name__ == "__main__":
    cli()
