from functools import wraps
from flask import abort, current_app, request, redirect, url_for, flash
from flask_login import current_user

def permission_required(permission_name):
    """
    Decorador que verifica si el usuario actual tiene un permiso específico.
    Si no, aborta con un error 403 (Forbidden).
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                # Si se requiere login para el permiso y no está autenticado
                flash("Debes iniciar sesión para acceder a esta página.", "warning")
                return redirect(url_for('auth.login', next=request.url))
            if not current_user.can(permission_name):
                current_app.logger.warning(
                    f"Acceso denegado para el usuario {current_user.email or 'Anónimo'} "
                    f"al recurso que requiere el permiso '{permission_name}'."
                )
                abort(403) # Forbidden
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """
    Decorador que verifica si el usuario actual es un administrador.
    Utiliza el permiso 'is_admin()' del modelo User, que a su vez chequea si el usuario
    tiene algún rol con `is_admin_role = True`.
    Si no, aborta con un error 403 (Forbidden).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Debes iniciar sesión como administrador para acceder a esta página.", "warning")
            return redirect(url_for('auth.login', next=request.url))
        if not current_user.is_admin():
            current_app.logger.warning(
                f"Acceso de administrador denegado para el usuario {current_user.email or 'Anónimo'}."
            )
            abort(403) # Forbidden
        return f(*args, **kwargs)
    return decorated_function

def approval_required(f):
    """
    Decorador que verifica si la cuenta del usuario actual ha sido aprobada.
    Si no, redirige a una página informativa o muestra un flash.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            # Esto debería ser manejado por @login_required usualmente antes de este decorador
            flash("Debes iniciar sesión para acceder a esta página.", "warning")
            return redirect(url_for('auth.login', next=request.url))
        if not current_user.is_approved:
            flash('Tu cuenta aún no ha sido aprobada. Por favor, espera la aprobación de un administrador.', 'warning')
            # Podrías redirigir a una página específica de "pendiente de aprobación"
            # o simplemente al dashboard/index donde el mensaje flash será visible.
            return redirect(url_for('main.index')) # O 'main.dashboard'
        return f(*args, **kwargs)
    return decorated_function
