import os
from dotenv import load_dotenv

load_dotenv() # Carga variables de entorno desde .env

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tu_super_secreto_key_aqui' # Cambiar en producción

    # Configuración de Base de Datos: Prioriza D1 si la variable de entorno está presente
    D1_DATABASE_URL = os.environ.get('D1_DATABASE_URL') # Ej: d1://<ACCOUNT_ID>/<DB_NAME> o un string de conexión para el driver
    if D1_DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = D1_DATABASE_URL
        # Podría necesitarse un driver específico para SQLAlchemy con D1, ej: 'sqlite+pysqlite:///:memory:' (no para D1 real)
        # O un dialecto como 'sqlite+cloudflare-d1://...' si existe.
        # Por ahora, asumimos que el string de conexión es suficiente o se adaptará.
        # Para D1, SQLAlchemy podría necesitar `connect_args={"check_same_thread": False}` si usa sqlite internamente.
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance/app.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuración de Subida de Archivos: Prioriza R2
    R2_BUCKET_NAME = os.environ.get('R2_BUCKET_NAME')
    R2_ACCOUNT_ID = os.environ.get('R2_ACCOUNT_ID')
    R2_ACCESS_KEY_ID = os.environ.get('R2_ACCESS_KEY_ID')
    R2_SECRET_ACCESS_KEY = os.environ.get('R2_SECRET_ACCESS_KEY')
    R2_PUBLIC_URL_BASE = os.environ.get('R2_PUBLIC_URL_BASE') # Ej: https://<id>.r2.cloudflarestorage.com/<bucket-name>

    # UPLOAD_FOLDER local solo como fallback si R2 no está configurado
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app/static/uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB para subidas de archivos

    # Configuración para el administrador inicial (cambiar en producción)
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@example.com'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'AdminPassword123!'

    # Roles y permisos (se pueden expandir)
    # Estos son solo ejemplos, la gestión real estará en la base de datos
    ROLES = {
        'Admin': ['manage_users', 'manage_roles', 'manage_forms', 'view_all_submissions', 'export_submissions'],
        'Editor': ['create_forms', 'edit_own_forms', 'view_own_submissions'],
        'Member': ['submit_forms', 'view_own_dashboard']
    }

    # Secciones del sitio para formularios
    FORM_SECTIONS = ["Site Survey", "Implementación", "Feedback General", "Soporte Técnico"]

    # Asegurarse de que la carpeta de subidas exista
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True # Para ver las consultas SQL generadas

class ProductionConfig(Config):
    DEBUG = False
    # Aquí se podrían añadir configuraciones específicas de producción
    # como logging avanzado, diferentes URLs de base de datos, etc.

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Base de datos en memoria para tests
    WTF_CSRF_ENABLED = False # Deshabilitar CSRF para tests de formularios si es necesario


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
