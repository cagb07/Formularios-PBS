from flask import render_template, redirect, request, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from . import auth # Blueprint 'auth'
from .. import db
from ..models import User, Role, Permission
from .forms import LoginForm, RegistrationForm, EditUserForm, RoleForm, AssignPermissionsToRoleForm
from ..decorators import admin_required, permission_required # Se crearán después

# --- Rutas de Autenticación ---
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Esta cuenta ha sido desactivada.', 'danger')
                return redirect(url_for('auth.login'))
            # No se verifica is_approved aquí, se verifica en el dashboard o al acceder a recursos.
            # Opcionalmente, se podría verificar aquí si se desea impedir el login completo.
            login_user(user, remember=form.remember_me.data)
            user.ping() # Actualizar last_seen
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.dashboard')
            flash('Has iniciado sesión correctamente.', 'success')
            return redirect(next_page)
        else:
            flash('Correo electrónico o contraseña incorrectos.', 'danger')
    return render_template('auth/login.html', title='Iniciar Sesión', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data.lower())
        user.set_password(form.password.data)
        # Los nuevos usuarios no están aprobados por defecto
        user.is_approved = False

        # Asignar rol por defecto (ej. 'Member')
        default_role = Role.query.filter_by(default=True).first()
        if default_role:
            user.roles.append(default_role)

        db.session.add(user)
        db.session.commit()
        # TODO: Enviar email al admin para aprobación / al usuario confirmando registro pendiente
        flash('Te has registrado exitosamente. Tu cuenta necesita ser aprobada por un administrador antes de que puedas iniciar sesión.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Registrarse', form=form)

# --- Rutas de Gestión de Usuarios (Admin) ---
@auth.route('/users')
@login_required
@admin_required # Decorador para asegurar que solo admins accedan
def manage_users():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('USERS_PER_PAGE', 10)
    pagination = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    users = pagination.items
    return render_template('auth/manage_users.html', users=users, pagination=pagination, title="Gestionar Usuarios")

@auth.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm(user=user) # Pasar el usuario al formulario para validación de email
    if form.validate_on_submit():
        user.email = form.email.data.lower()
        # user.first_name = form.first_name.data
        # user.last_name = form.last_name.data
        user.is_approved = form.is_approved.data
        user.is_active = form.is_active.data

        # Actualizar roles
        current_roles_ids = {role.id for role in user.roles}
        selected_roles_ids = set(form.roles.data)

        # Roles a añadir
        for role_id in selected_roles_ids - current_roles_ids:
            role_to_add = Role.query.get(role_id)
            if role_to_add:
                user.roles.append(role_to_add)

        # Roles a quitar
        for role_id in current_roles_ids - selected_roles_ids:
            # Prevenir quitar el último rol de Admin al último Admin activo
            role_to_remove = Role.query.get(role_id)
            if role_to_remove and role_to_remove.name == 'Admin':
                # Contar cuántos admins activos quedan
                admin_role = Role.query.filter_by(name='Admin').first()
                if admin_role:
                    active_admins_count = User.query.join(User.roles).filter(Role.id == admin_role.id, User.is_active == True).count()
                    if user.has_role('Admin') and user.is_active and active_admins_count <= 1:
                        flash('No se puede quitar el rol "Admin" al último administrador activo.', 'danger')
                        return redirect(url_for('auth.edit_user', user_id=user.id))

            if role_to_remove:
                user.roles.remove(role_to_remove)

        db.session.add(user)
        db.session.commit()
        flash(f'Usuario {user.email} actualizado correctamente.', 'success')
        return redirect(url_for('auth.manage_users'))

    # Pre-llenar el formulario con los datos del usuario
    form.email.data = user.email
    # form.first_name.data = user.first_name
    # form.last_name.data = user.last_name
    form.is_approved.data = user.is_approved
    form.is_active.data = user.is_active
    form.roles.data = [role.id for role in user.roles]

    return render_template('auth/edit_user.html', form=form, user=user, title="Editar Usuario")


@auth.route('/user/<int:user_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    if not user.is_approved:
        user.is_approved = True
        db.session.commit()
        flash(f'Usuario {user.email} ha sido aprobado.', 'success')
        # TODO: Enviar email al usuario notificando la aprobación
    else:
        flash(f'Usuario {user.email} ya estaba aprobado.', 'info')
    return redirect(url_for('auth.manage_users'))

@auth.route('/user/<int:user_id>/toggle_active', methods=['POST'])
@login_required
@admin_required
def toggle_active_user(user_id):
    user = User.query.get_or_404(user_id)

    # Prevenir desactivar al último administrador activo
    if user.is_active and user.is_admin():
        admin_role = Role.query.filter_by(name='Admin').first()
        if admin_role:
            active_admins_count = User.query.join(User.roles).filter(Role.id == admin_role.id, User.is_active == True).count()
            if active_admins_count <= 1 and user.id == User.query.join(User.roles).filter(Role.id == admin_role.id, User.is_active == True).first().id :
                flash('No se puede desactivar al último administrador activo.', 'danger')
                return redirect(url_for('auth.manage_users'))

    user.is_active = not user.is_active
    db.session.commit()
    status = "activado" if user.is_active else "desactivado"
    flash(f'Usuario {user.email} ha sido {status}.', 'success')
    return redirect(url_for('auth.manage_users'))


@auth.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user_to_delete = User.query.get_or_404(user_id)

    if user_to_delete.id == current_user.id:
        flash('No puedes eliminar tu propia cuenta de administrador.', 'danger')
        return redirect(url_for('auth.manage_users'))

    # Prevenir eliminar al último administrador
    if user_to_delete.is_admin():
        admin_role = Role.query.filter_by(name='Admin').first()
        if admin_role:
            # Contar todos los administradores (activos o no, para ser más seguro)
            total_admins_count = User.query.join(User.roles).filter(Role.id == admin_role.id).count()
            if total_admins_count <= 1:
                flash('No se puede eliminar al último administrador.', 'danger')
                return redirect(url_for('auth.manage_users'))

    # Aquí se podrían eliminar datos asociados al usuario o anonimizarlos
    # Por ahora, solo eliminamos el usuario.
    # Considerar soft delete (marcar como eliminado en lugar de borrar físicamente)

    email = user_to_delete.email
    db.session.delete(user_to_delete)
    db.session.commit()
    flash(f'Usuario {email} ha sido eliminado.', 'success')
    return redirect(url_for('auth.manage_users'))


# --- Rutas de Gestión de Roles y Permisos (Admin) ---
@auth.route('/roles')
@login_required
@admin_required
def manage_roles():
    roles = Role.query.order_by(Role.name).all()
    return render_template('auth/manage_roles.html', roles=roles, title="Gestionar Roles")

@auth.route('/role/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_role():
    form = RoleForm()
    if form.validate_on_submit():
        role = Role(name=form.name.data, is_admin_role=form.is_admin_role.data)
        # Asignar permisos seleccionados
        for perm_id in form.permissions.data:
            permission = Permission.query.get(perm_id)
            if permission:
                role.permissions.append(permission)
        db.session.add(role)
        db.session.commit()
        flash(f'Rol "{role.name}" creado exitosamente.', 'success')
        return redirect(url_for('auth.manage_roles'))
    return render_template('auth/create_edit_role.html', form=form, title="Crear Rol", action="Crear")


@auth.route('/role/<int:role_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_role(role_id):
    role = Role.query.get_or_404(role_id)
    form = RoleForm(role=role) # Pasar el rol para validación de nombre

    if form.validate_on_submit():
        role.name = form.name.data
        role.is_admin_role = form.is_admin_role.data

        # Actualizar permisos
        current_permission_ids = {perm.id for perm in role.permissions}
        selected_permission_ids = set(form.permissions.data)

        # Permisos a añadir
        for perm_id in selected_permission_ids - current_permission_ids:
            permission_to_add = Permission.query.get(perm_id)
            if permission_to_add:
                role.permissions.append(permission_to_add)

        # Permisos a quitar
        for perm_id in current_permission_ids - selected_permission_ids:
            permission_to_remove = Permission.query.get(perm_id)
            if permission_to_remove:
                role.permissions.remove(permission_to_remove)

        db.session.add(role)
        db.session.commit()
        flash(f'Rol "{role.name}" actualizado exitosamente.', 'success')
        return redirect(url_for('auth.manage_roles'))

    form.name.data = role.name
    form.is_admin_role.data = role.is_admin_role
    form.permissions.data = [perm.id for perm in role.permissions]
    return render_template('auth/create_edit_role.html', form=form, role=role, title="Editar Rol", action="Actualizar")

@auth.route('/role/<int:role_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_role(role_id):
    role_to_delete = Role.query.get_or_404(role_id)

    if role_to_delete.name == 'Admin': # Prevenir borrar el rol Admin principal
        flash('El rol "Admin" no puede ser eliminado.', 'danger')
        return redirect(url_for('auth.manage_roles'))

    if role_to_delete.users.count() > 0:
        flash(f'El rol "{role_to_delete.name}" está asignado a usuarios y no puede ser eliminado. Reasigna los usuarios a otros roles primero.', 'warning')
        return redirect(url_for('auth.manage_roles'))

    name = role_to_delete.name
    db.session.delete(role_to_delete)
    db.session.commit()
    flash(f'Rol "{name}" ha sido eliminado.', 'success')
    return redirect(url_for('auth.manage_roles'))


# --- Permisos (Generalmente se definen en el sistema y no se gestionan por UI, pero se puede añadir) ---
# Si se necesita una UI para gestionar Permisos (crear nuevos permisos en runtime):
@auth.route('/permissions')
@login_required
@admin_required
def manage_permissions():
    # Esta es una vista opcional. Normalmente los permisos son definidos por el desarrollador.
    permissions = Permission.query.order_by(Permission.name).all()
    return render_template('auth/manage_permissions.html', permissions=permissions, title="Gestionar Permisos")

# Un endpoint para inicializar roles y permisos (llamado desde un comando CLI usualmente)
@auth.route('/init_rbac')
@login_required
@admin_required # Solo un admin puede re-inicializar esto
def init_rbac():
    try:
        Role.insert_roles(current_app.config['ROLES'])
        # Crear usuario admin si no existe
        admin_email = current_app.config['ADMIN_EMAIL']
        admin_user = User.query.filter_by(email=admin_email).first()
        if not admin_user:
            admin_password = current_app.config['ADMIN_PASSWORD']
            admin = User(email=admin_email, is_approved=True, is_active=True)
            admin.set_password(admin_password)
            admin_role = Role.query.filter_by(name='Admin').first()
            if admin_role:
                admin.roles.append(admin_role)
            db.session.add(admin)
            db.session.commit()
            flash('Usuario administrador por defecto creado/verificado.', 'info')
        flash('Roles y permisos básicos inicializados/verificados.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al inicializar RBAC: {e}', 'danger')
        current_app.logger.error(f"Error en init_rbac: {e}")
    return redirect(url_for('auth.manage_roles'))


# Es importante añadir los templates HTML para estas rutas:
# - auth/login.html
# - auth/register.html
# - auth/manage_users.html
# - auth/edit_user.html
# - auth/manage_roles.html
# - auth/create_edit_role.html (unificado para crear y editar)
# - (opcional) auth/manage_permissions.html

# También se necesita crear el archivo app/decorators.py con @admin_required y @permission_required.
