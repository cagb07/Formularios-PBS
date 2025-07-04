from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField, FieldList, FormField, HiddenField, MultipleFileField
from wtforms.validators import DataRequired, Length, Optional, Regexp
from app.models import Category, FormDefinition # Para choices dinámicos
from flask import current_app

class CategoryForm(FlaskForm):
    name = StringField('Nombre de la Categoría', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descripción (Opcional)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Guardar Categoría')

    def validate_name(self, field):
        from app.models import Category # Evitar importación circular
        existing_category = Category.query.filter(Category.name == field.data, Category.id != (self.id.data if self.id and self.id.data else None)).first()
        if existing_category:
            raise ValidationError('Ya existe una categoría con este nombre.')

    # Para edición, se podría añadir un campo oculto para el ID
    id = HiddenField('ID')


class FormFieldDefinitionForm(FlaskForm):
    """Subformulario para definir un campo individual dentro de un FormDefinition."""
    field_label = StringField('Etiqueta del Campo', validators=[DataRequired(), Length(max=255)],
                              description="Texto que verá el usuario (ej: 'Nombre Completo').")
    field_name = StringField('Nombre Interno del Campo',
                             validators=[DataRequired(), Length(max=100),
                                         Regexp('^[a-z0-9_]+$', message="Solo minúsculas, números y guiones bajos (ej: 'customer_name').")],
                             description="Nombre único para guardar datos, sin espacios ni caracteres especiales.")
    field_type = SelectField('Tipo de Campo', validators=[DataRequired()], choices=[
        ('text', 'Texto Corto (Text)'),
        ('textarea', 'Texto Largo (Textarea)'),
        ('number', 'Número (Number)'),
        ('date', 'Fecha (Date)'),
        ('boolean', 'Booleano (Sí/No)'),
        ('image_upload', 'Subida de Imagen (Una o Múltiples)')
    ])
    is_required = BooleanField('Requerido', default=False)
    # order = IntegerField('Orden', default=0) # El orden se manejará por la lista

class FormDefinitionForm(FlaskForm):
    name = StringField('Nombre de la Plantilla del Formulario', validators=[DataRequired(), Length(max=150)],
                       description="Título principal del formulario (ej: 'Encuesta de Satisfacción Cliente').")
    description = TextAreaField('Descripción (Opcional)', validators=[Optional(), Length(max=1000)],
                                description="Instrucciones o detalles adicionales sobre el formulario.")
    category_id = SelectField('Categoría (Opcional)', coerce=int, validators=[Optional()],
                              description="Agrupa formularios similares.")
    section = SelectField('Sección del Sitio (Opcional)', validators=[Optional()], choices=[],
                          description="Dónde aparecerá este formulario en la aplicación.")

    fields = FieldList(FormField(FormFieldDefinitionForm), min_entries=1, label="Campos del Formulario")

    is_active = BooleanField('Activo (los usuarios pueden verlo y enviarlo)', default=True)
    submit = SubmitField('Guardar Plantilla de Formulario')

    def __init__(self, *args, **kwargs):
        super(FormDefinitionForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]
        self.category_id.choices.insert(0, (0, '--- Sin Categoría ---')) # Opción para no asignar categoría

        # Cargar secciones desde la configuración de la app
        site_sections = current_app.config.get('FORM_SECTIONS', [])
        self.section.choices = [("", "--- Sin Sección ---")] + [(s, s) for s in site_sections]

    def validate_name(self, field):
        # Validar que el nombre de la plantilla sea único (opcional, pero buena idea)
        # from app.models import FormDefinition # Evitar importación circular
        # existing_form = FormDefinition.query.filter(FormDefinition.name == field.data, FormDefinition.id != (self.id.data if hasattr(self, 'id') and self.id.data else None)).first()
        # if existing_form:
        #     raise ValidationError('Ya existe una plantilla de formulario con este nombre.')
        pass # Por ahora no se valida unicidad del nombre de la plantilla

    def validate_fields(self, field_list):
        # Validar que los field_name sean únicos dentro de este formulario
        field_names = set()
        for i, field_entry in enumerate(field_list.entries):
            f_name = field_entry.form.field_name.data
            if f_name:
                if f_name in field_names:
                    # Añadir error al campo específico
                    field_list.entries[i].form.field_name.errors.append(f"El nombre interno del campo '{f_name}' está duplicado en esta plantilla.")
                    # También se puede añadir un error general al FieldList si se prefiere
                    # raise ValidationError(f"El nombre interno del campo '{f_name}' está duplicado.")
                field_names.add(f_name)


# --- Formularios para rellenar por el usuario (se generan dinámicamente) ---
# No se define una clase FlaskForm estática aquí, sino que se construirá en las rutas.
# Sin embargo, podríamos tener un formulario base si hay elementos comunes.

class DynamicFormSubmission(FlaskForm):
    """
    Esta clase se usará como base y se le añadirán campos dinámicamente
    en la ruta `submit_form` antes de instanciarla.
    """
    # Campo oculto para el ID de la definición del formulario que se está enviando
    form_definition_id = HiddenField(validators=[DataRequired()])

    submit = SubmitField('Enviar Formulario')

    # Método para añadir campos dinámicamente
    @classmethod
    def append_field(cls, name, field):
        setattr(cls, name, field)

    # Método para quitar campos (útil si se reutiliza la clase para diferentes forms)
    @classmethod
    def remove_field(cls, name):
        if hasattr(cls, name):
            delattr(cls, name)


# Ejemplo de cómo se añadirían campos a DynamicFormSubmission en la ruta:
#
# from wtforms import StringField, IntegerField, DateField, TextAreaField, BooleanField, FileField
# from wtforms.validators import DataRequired, Optional, Email, NumberRange
# from flask_wtf.file import FileAllowed
#
# ... en la ruta ...
# form_def = FormDefinition.query.get_or_404(form_def_id)
# submission_form = DynamicFormSubmission(form_definition_id=form_def.id) # Pasar el ID
#
# for field_def in form_def.fields.order_by(FormField.order):
#     validators = []
#     if field_def.is_required:
#         validators.append(DataRequired(message=f"El campo '{field_def.label}' es obligatorio."))
#
#     wtform_field = None
#     if field_def.field_type == 'text':
#         wtform_field = StringField(field_def.label, validators=validators)
#     elif field_def.field_type == 'textarea':
#         wtform_field = TextAreaField(field_def.label, validators=validators)
#     elif field_def.field_type == 'number':
#         validators.append(Optional()) # Para que no falle si no es requerido y está vacío
#         wtform_field = IntegerField(field_def.label, validators=validators) # O DecimalField
#     elif field_def.field_type == 'date':
#         validators.append(Optional())
#         wtform_field = DateField(field_def.label, format='%Y-%m-%d', validators=validators)
#     elif field_def.field_type == 'boolean':
#         # BooleanField no necesita DataRequired si es opcional, su valor será True/False
#         wtform_field = BooleanField(field_def.label) # No se suele poner DataRequired
#     elif field_def.field_type == 'image_upload':
#         allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
#         # MultipleFileField para varias imágenes
#         wtform_field = MultipleFileField(field_def.label,
#                                          validators=validators + [FileAllowed(allowed_extensions, '¡Solo imágenes!')])
#
#     if wtform_field:
#         DynamicFormSubmission.append_field(field_def.field_name, wtform_field)
#
# # Al final, instanciar el formulario después de añadir todos los campos
# current_dynamic_form = DynamicFormSubmission()
#
# # Y después de usarlo, es buena idea limpiar los campos para la próxima vez que se use la clase base
# for field_def in form_def.fields:
#     DynamicFormSubmission.remove_field(field_def.field_name)
#
# Esto es un poco complejo. Una alternativa es crear una nueva clase dinámicamente cada vez:
#
# def create_dynamic_form_class(form_definition):
#     class TempDynamicForm(DynamicFormSubmission):
#         pass
#
#     for field_def in form_definition.fields.order_by(FormField.order):
#         # ... (lógica de creación de wtform_field igual que arriba) ...
#         if wtform_field:
#             setattr(TempDynamicForm, field_def.field_name, wtform_field)
#     return TempDynamicForm
#
# ... en la ruta ...
# DynamicFormClass = create_dynamic_form_class(form_def)
# current_dynamic_form = DynamicFormClass(form_definition_id=form_def.id)
#
# Esta segunda aproximación es más limpia y evita problemas de estado entre requests.

class ExportForm(FlaskForm):
    submission_id = HiddenField(validators=[DataRequired()])
    submit = SubmitField('Exportar a Word')
