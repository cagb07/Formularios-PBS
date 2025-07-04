from app import create_app, db
from app.models import User, Role, Permission # Asegúrate que todos los modelos estén importados
from config import config as app_config # Renombrado para evitar conflicto de nombres
import os

# Selecciona la configuración (development, production, testing)
config_name = os.getenv('FLASK_CONFIG') or 'default'
app = create_app(config_name)

@app.shell_context_processor
def make_shell_context():
    # Añadir todos los modelos necesarios en el shell
    return dict(db=db, User=User, Role=Role, Permission=Permission,
                Category=getattr(__import__('app.models', fromlist=['Category']), 'Category', None),
                FormDefinition=getattr(__import__('app.models', fromlist=['FormDefinition']), 'FormDefinition', None),
                FormField=getattr(__import__('app.models', fromlist=['FormField']), 'FormField', None),
                FormSubmission=getattr(__import__('app.models', fromlist=['FormSubmission']), 'FormSubmission', None),
                SubmissionData=getattr(__import__('app.models', fromlist=['SubmissionData']), 'SubmissionData', None),
                UploadedImage=getattr(__import__('app.models', fromlist=['UploadedImage']), 'UploadedImage', None)
                )

@app.cli.command("init-db")
def init_db_command():
    """Inicializa la base de datos, crea tablas, roles y permisos básicos."""
    with app.app_context(): # Asegurar que estamos dentro del contexto de la aplicación
        db.create_all()
        print("Base de datos y tablas creadas.")

        # Poblar roles y permisos usando el método estático de Role
        # Pasar el diccionario ROLES desde la configuración de la app
        Role.insert_roles(app.config['ROLES'])
        print("Roles y permisos por defecto creados/actualizados.")

@app.cli.command("create-admin")
def create_admin_command():
    """Crea el usuario administrador inicial si no existe."""
    with app.app_context(): # Contexto de aplicación
        admin_email = app.config['ADMIN_EMAIL']
        admin_password = app.config['ADMIN_PASSWORD']

        if User.query.filter_by(email=admin_email).first():
            print(f"El usuario administrador '{admin_email}' ya existe.")
            return

        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            print("Rol 'Admin' no encontrado. Ejecuta 'flask init-db' primero para crear roles.")
            # Alternativamente, se podría crear el rol Admin aquí si es crítico
            # admin_role = Role(name='Admin', is_admin_role=True)
            # # Asignar todos los permisos definidos en config al rol Admin
            # for perm_name in app.config['ROLES'].get('Admin', []):
            #     perm = Permission.query.filter_by(name=perm_name).first()
            #     if not perm:
            #         perm = Permission(name=perm_name)
            #         db.session.add(perm)
            #     if perm not in admin_role.permissions:
            #         admin_role.permissions.append(perm)
            # db.session.add(admin_role)
            # db.session.commit()
            # print("Rol 'Admin' creado.")
            return

        admin_user = User(email=admin_email, is_approved=True, is_active=True)
        admin_user.set_password(admin_password)
        admin_user.roles.append(admin_role)

        db.session.add(admin_user)
        db.session.commit()
        print(f"Usuario administrador '{admin_email}' creado con éxito.")

if __name__ == '__main__':
    app.run()
