from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager # Import db y login_manager desde app package
import datetime

# Tabla de asociación para la relación muchos-a-muchos entre Usuarios y Roles
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

# Tabla de asociación para la relación muchos-a-muchos entre Roles y Permisos
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)

class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True, nullable=False) # Ej: 'manage_users', 'submit_forms'
    description = db.Column(db.String(255)) # Descripción opcional del permiso

    def __repr__(self):
        return f'<Permission {self.name}>'

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True, nullable=False) # Ej: 'Admin', 'Editor', 'Member'
    is_admin_role = db.Column(db.Boolean, default=False) # Para identificar fácilmente el rol de superadmin
    default = db.Column(db.Boolean, default=False, index=True) # Si este rol se asigna por defecto a nuevos usuarios
    permissions = db.relationship('Permission', secondary=role_permissions,
                                  backref=db.backref('roles', lazy='dynamic'),
                                  lazy='dynamic')
    users = db.relationship('User', secondary=user_roles,
                            backref=db.backref('roles', lazy='dynamic'), # Cambio de 'roles_assigned' a 'roles' para consistencia
                            lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = []

    def add_permission(self, perm):
        if not self.has_permission(perm.name):
            self.permissions.append(perm)

    def remove_permission(self, perm):
        if self.has_permission(perm.name):
            self.permissions.remove(perm)

    def has_permission(self, permission_name):
        return self.permissions.filter(Permission.name == permission_name).first() is not None

    @staticmethod
    def insert_roles(app_config_roles):
        # app_config_roles es el diccionario Config.ROLES
        roles = {
            'Member': Role(name='Member', default=True),
            'Editor': Role(name='Editor'),
            'Admin': Role(name='Admin', is_admin_role=True)
        }
        default_role = 'Member'

        for r_name in roles:
            role = Role.query.filter_by(name=r_name).first()
            if role is None:
                role = roles[r_name]
            role.default = (role.name == default_role)
            role.is_admin_role = (role.name == 'Admin') # Asegurar que Admin sea is_admin_role

            # Asignar permisos basados en la configuración
            if r_name in app_config_roles:
                for perm_name in app_config_roles[r_name]:
                    permission = Permission.query.filter_by(name=perm_name).first()
                    if permission is None:
                        permission = Permission(name=perm_name)
                        db.session.add(permission)
                    if not role.has_permission(perm_name):
                        role.add_permission(permission)
            db.session.add(role)
        db.session.commit()


    def __repr__(self):
        return f'<Role {self.name}>'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    is_approved = db.Column(db.Boolean, default=False) # Requiere aprobación del admin
    is_active = db.Column(db.Boolean, default=True) # Para desactivar cuentas en lugar de borrarlas
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relación con roles ya definida por el backref de Role.users

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if not self.roles: # Si no se asignaron roles explícitamente
            default_role = Role.query.filter_by(default=True).first()
            if default_role:
                self.roles.append(default_role)


    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def set_password(self, password): # Método explícito preferido en la app
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can(self, permission_name):
        """Verifica si el usuario tiene un permiso específico."""
        for role in self.roles:
            if role.has_permission(permission_name):
                return True
        return False

    def has_role(self, role_name):
        """Verifica si el usuario tiene un rol específico."""
        return self.roles.filter(Role.name == role_name).first() is not None

    def is_admin(self):
        """Verifica si el usuario tiene algún rol que sea de administrador."""
        for role in self.roles:
            if role.is_admin_role:
                return True
        return False

    def ping(self):
        self.last_seen = datetime.datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f'<User {self.email}>'

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_admin(self):
        return False

    def has_role(self, role_name):
        return False

    @property
    def is_approved(self):
        return False

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- Modelos para Formularios Dinámicos ---

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    # Relación con FormDefinition
    form_definitions = db.relationship('FormDefinition', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'

class FormDefinition(db.Model):
    __tablename__ = 'form_definitions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True) # Puede no tener categoría
    section = db.Column(db.String(100), nullable=True) # Ej: "Site Survey", "Implementación"
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id')) # Quién creó/editó la plantilla
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True) # Para activar/desactivar formularios

    creator = db.relationship('User', backref='created_form_definitions')
    fields = db.relationship('FormField', backref='form_definition', lazy='dynamic', cascade="all, delete-orphan")
    submissions = db.relationship('FormSubmission', backref='form_definition', lazy='dynamic')

    def __repr__(self):
        return f'<FormDefinition {self.name}>'

class FormField(db.Model):
    __tablename__ = 'form_fields'
    id = db.Column(db.Integer, primary_key=True)
    form_definition_id = db.Column(db.Integer, db.ForeignKey('form_definitions.id'), nullable=False)
    label = db.Column(db.String(255), nullable=False) # El texto que ve el usuario para el campo
    field_name = db.Column(db.String(100), nullable=False) # Nombre interno, usado para guardar datos (ej. 'customer_name')
    field_type = db.Column(db.String(50), nullable=False) # 'text', 'number', 'date', 'textarea', 'boolean', 'image_upload'
    is_required = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0) # Para ordenar los campos en el formulario
    # Opciones adicionales (ej. para selects, radios, o validaciones específicas)
    # options = db.Column(db.Text, nullable=True) # Podría ser un JSON string

    def __repr__(self):
        return f'<FormField {self.label} ({self.field_type}) for Form ID {self.form_definition_id}>'

class FormSubmission(db.Model):
    __tablename__ = 'form_submissions'
    id = db.Column(db.Integer, primary_key=True)
    form_definition_id = db.Column(db.Integer, db.ForeignKey('form_definitions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # Quién envió el formulario
    submitted_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    submitter = db.relationship('User', backref='form_submissions')
    data_entries = db.relationship('SubmissionData', backref='submission', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<FormSubmission ID {self.id} for FormDef ID {self.form_definition_id} by User ID {self.user_id}>'

class SubmissionData(db.Model):
    __tablename__ = 'submission_data'
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('form_submissions.id'), nullable=False)
    field_id = db.Column(db.Integer, db.ForeignKey('form_fields.id'), nullable=False) # Enlaza al FormField original
    field_name = db.Column(db.String(100), nullable=False) # Denormalizado para fácil acceso, el nombre del campo cuando se envió
    value_text = db.Column(db.Text, nullable=True) # Para tipos texto, textarea, date, number (convertido), boolean (convertido)
    # No almacenamos directamente imágenes aquí, sino sus rutas o referencias.

    # Relación con las imágenes subidas para este campo específico de esta sumisión
    uploaded_images = db.relationship('UploadedImage', backref='submission_data_entry', lazy='dynamic', cascade="all, delete-orphan")

    field = db.relationship('FormField') # Para poder acceder a la definición del campo si es necesario

    def __repr__(self):
        return f'<SubmissionData for Submission ID {self.submission_id}, Field {self.field_name}>'

class UploadedImage(db.Model):
    __tablename__ = 'uploaded_images'
    id = db.Column(db.Integer, primary_key=True)
    submission_data_id = db.Column(db.Integer, db.ForeignKey('submission_data.id'), nullable=False) # A qué entrada de datos pertenece
    filename = db.Column(db.String(255), nullable=False) # Nombre del archivo guardado en el servidor
    original_filename = db.Column(db.String(255), nullable=True) # Nombre original del archivo
    mimetype = db.Column(db.String(100))
    uploaded_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<UploadedImage {self.filename}>'
