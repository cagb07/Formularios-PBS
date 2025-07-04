from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import config # Importa el diccionario de configuraciones
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login' # Blueprint 'auth', ruta 'login'
login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."
login_manager.login_message_category = "info" # Categoría de mensaje para Bootstrap

csrf = CSRFProtect()

def create_app(config_name='default'):
    """
    Factory de la aplicación Flask.
    """
    app = Flask(__name__, instance_relative_config=True)

    # Cargar configuración
    app.config.from_object(config[config_name])

    # Crear la carpeta 'instance' si no existe, para SQLite y otros archivos de instancia
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Crear la carpeta de subidas si no existe
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    # Si usas Flask-Migrate:
    # from flask_migrate import Migrate
    # migrate = Migrate(app, db)

    # Registrar Blueprints
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .forms_management import forms_bp as forms_management_blueprint
    app.register_blueprint(forms_management_blueprint, url_prefix='/forms')

    # (Opcional) Registrar un blueprint para errores
    # from .errors import errors as errors_blueprint
    # app.register_blueprint(errors_blueprint)

    # Configuración adicional de la app (ej. logging, etc.) si es necesario

    return app
