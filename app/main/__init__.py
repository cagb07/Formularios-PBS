from flask import Blueprint

main = Blueprint('main', __name__)

from . import routes # Importa las rutas del blueprint principal
