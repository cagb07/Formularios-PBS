from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectMultipleField, widgets
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User, Role

class LoginForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[DataRequired(), Length(1, 120), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recuérdame')
    submit = SubmitField('Iniciar Sesión')

class RegistrationForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[DataRequired(), Length(1, 120), Email()])
    # first_name = StringField('Nombre', validators=[DataRequired(), Length(1, 64)])
    # last_name = StringField('Apellido', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('Contraseña', validators=[
        DataRequired(),
        EqualTo('password2', message='Las contraseñas deben coincidir.')
    ])
    password2 = PasswordField('Confirmar Contraseña', validators=[DataRequired()])
    submit = SubmitField('Registrarse')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Este correo electrónico ya está registrado.')

class EditUserForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[DataRequired(), Length(1, 120), Email()])
    # first_name = StringField('Nombre', validators=[DataRequired(), Length(1, 64)])
    # last_name = StringField('Apellido', validators=[DataRequired(), Length(1, 64)])
    is_approved = BooleanField('Aprobado')
    is_active = BooleanField('Activo')
    roles = SelectMultipleField('Roles', coerce=int, widget=widgets.ListWidget(prefix_label=False), option_widget=widgets.CheckboxInput())
    submit = SubmitField('Actualizar Usuario')

    def __init__(self, user, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.roles.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.original_email = user.email
        self.user = user # Guardar el usuario para validación

    def validate_email(self, field):
        if field.data.lower() != self.original_email.lower():
            if User.query.filter_by(email=field.data.lower()).first():
                raise ValidationError('Este correo electrónico ya está en uso por otra cuenta.')

class RoleForm(FlaskForm):
    name = StringField('Nombre del Rol', validators=[DataRequired(), Length(1, 64)])
    # description = StringField('Descripción (opcional)', validators=[Length(0, 255)])
    is_admin_role = BooleanField('Es un rol de Administrador')
    permissions = SelectMultipleField('Permisos', coerce=int, widget=widgets.ListWidget(prefix_label=False), option_widget=widgets.CheckboxInput())
    submit = SubmitField('Guardar Rol')

    def __init__(self, role=None, *args, **kwargs):
        super(RoleForm, self).__init__(*args, **kwargs)
        from app.models import Permission # Evitar importación circular
        self.permissions.choices = [(p.id, p.name) for p in Permission.query.order_by(Permission.name).all()]
        self.original_name = role.name if role else None
        self.role = role

    def validate_name(self, field):
        if field.data != self.original_name:
            if Role.query.filter_by(name=field.data).first():
                raise ValidationError('Este nombre de rol ya está en uso.')

class AssignPermissionsToRoleForm(FlaskForm):
    role = None # Se seteará en la ruta
    permissions = SelectMultipleField('Permisos', coerce=int, widget=widgets.ListWidget(prefix_label=False), option_widget=widgets.CheckboxInput())
    submit = SubmitField('Actualizar Permisos del Rol')

    def __init__(self, role_obj, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role = role_obj
        from app.models import Permission
        all_permissions = Permission.query.order_by(Permission.name).all()
        self.permissions.choices = [(p.id, p.name) for p in all_permissions]
        # Pre-seleccionar los permisos que el rol ya tiene
        if kwargs.get('obj') is None and role_obj: # Solo si no se está cargando desde data
             self.permissions.data = [p.id for p in role_obj.permissions]
