from flask import Blueprint

auth = Blueprint('auth', __name__)

from . import routes, forms # Importa rutas y formularios del blueprint de autenticación
