from flask import Blueprint

forms_bp = Blueprint('forms_management', __name__)

from . import routes, forms # Importa rutas y formularios del blueprint de gestión de formularios
