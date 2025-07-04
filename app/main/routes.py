from flask import render_template, redirect, url_for, flash, current_app, g
from flask_login import current_user, login_required
from . import main # Blueprint 'main'
from app import db # SQLAlchemy instance
from app.models import FormDefinition, FormSubmission # Suponiendo estos modelos
import datetime

@main.before_app_request
def before_request():
    g.request_start_time = datetime.datetime.utcnow()
    # Podrías añadir más cosas a 'g' si son necesarias en toda la app durante una request
    # por ejemplo, g.user = current_user


@main.route('/')
@main.route('/index')
def index():
    # Si el usuario está autenticado y aprobado, quizás redirigir al dashboard
    # if current_user.is_authenticated and current_user.is_approved:
    #     return redirect(url_for('main.dashboard'))
    return render_template('main/index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_approved:
        flash('Tu cuenta aún no ha sido aprobada por un administrador.', 'warning')
        return redirect(url_for('main.index')) # O a una página de espera

    # Ejemplo de estadísticas para el dashboard
    try:
        total_forms_available = FormDefinition.query.filter_by(is_active=True).count()
        user_forms_submitted = FormSubmission.query.filter_by(user_id=current_user.id).count()
    except Exception as e:
        current_app.logger.error(f"Error al obtener estadísticas del dashboard: {e}")
        total_forms_available = "Error"
        user_forms_submitted = "Error"
        flash("No se pudieron cargar algunas estadísticas del dashboard.", "danger")


    stats = {
        'total_forms_available': total_forms_available,
        'user_forms_submitted': user_forms_submitted
    }
    return render_template('main/dashboard.html', title='Dashboard', stats=stats)

# Aquí podrían ir otras rutas generales de la aplicación, como 'about', 'contact', etc.
# Ejemplo:
# @main.route('/about')
# def about():
#     return render_template('main/about.html', title='Acerca de')

# Es importante que el modelo User tenga el método is_approved y has_role
# que se usa en base.html y aquí. Estos se definirán en app/models.py.
