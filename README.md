# Plataforma de Formularios Dinámicos con Flask y Cloudflare

Esta aplicación web, construida con Flask, proporciona una plataforma integral para el registro de usuarios, creación dinámica de formularios y recopilación de datos, con un robusto sistema de control de acceso basado en roles. Está diseñada para ser desplegable en Cloudflare Pages con Funciones Python, utilizando Cloudflare D1 para la base de datos y Cloudflare R2 para el almacenamiento de archivos.

## Características Principales

1.  **Autenticación y Gestión de Usuarios:**
    *   Registro e inicio de sesión local con correo electrónico y contraseña.
    *   Aprobación de nuevas cuentas por un administrador.
    *   Control de Acceso Basado en Roles (RBAC): Administrador, Editor, Miembro (por defecto).
    *   Gestión de usuarios (aprobar, activar/desactivar, asignar roles, eliminar) por administradores.
    *   Gestión de roles y permisos por administradores.
    *   Hashing seguro de contraseñas (bcrypt).

2.  **Creación Dinámica de Formularios y Recopilación de Datos:**
    *   Categorías de formularios definidas por el administrador.
    *   Asignación de formularios a secciones del sitio (ej., "Site Survey", "Implementación").
    *   Diseño de plantillas de formulario personalizadas por administradores/editores sin codificación:
        *   Tipos de campo: Texto, Número, Fecha, Área de Texto, Booleano (Sí/No), Subida de Imágenes (múltiples).
        *   Campos marcados como obligatorios.
    *   Envío de formularios por usuarios autenticados y aprobados.
    *   Visualización de datos enviados por administradores en tablas estructuradas.
    *   Miniaturas de imágenes en la vista de envíos.
    *   Exportación de envíos individuales a documentos Microsoft Word (.docx) con imágenes incrustadas.

3.  **Panel de Control (Dashboard):**
    *   Estadísticas: Total de formularios disponibles, total de envíos del usuario actual.
    *   Mensaje de bienvenida y accesos rápidos según el rol del usuario.

4.  **Interfaz de Usuario:**
    *   Idioma principal: Español.
    *   Tema Oscuro ("True Black/Tech") moderno y responsivo.
    *   Diseño adaptable a dispositivos móviles (Bootstrap 5).

## Estructura del Proyecto

```
.
├── app/                      # Módulo principal de la aplicación Flask
│   ├── __init__.py           # Factory de la aplicación (create_app)
│   ├── auth/                 # Blueprint para autenticación y gestión de usuarios/roles
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   ├── routes.py
│   │   └── templates/auth/   # Plantillas HTML para autenticación
│   ├── forms_management/     # Blueprint para creación y gestión de formularios
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   ├── routes.py
│   │   └── templates/forms_management/ # Plantillas HTML para formularios
│   ├── main/                 # Blueprint para rutas principales (index, dashboard)
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── templates/main/   # Plantillas HTML principales
│   ├── static/               # Archivos estáticos (CSS, JS, imágenes de UI)
│   ├── templates/            # Plantillas HTML base y compartidas
│   │   ├── base.html         # Plantilla base principal
│   │   └── bootstrap_wtf.html # Macro para renderizar formularios WTForms con Bootstrap
│   ├── decorators.py         # Decoradores personalizados (ej. @admin_required)
│   └── models.py             # Modelos de SQLAlchemy (User, Role, FormDefinition, etc.)
├── functions/                # Para Cloudflare Pages Functions
│   └── [[path]].py           # Handler Python para rutas dinámicas en Cloudflare Pages
├── instance/                 # Archivos de instancia (ej. app.db si se usa SQLite localmente)
├── migrations/               # (Opcional) Si se usa Flask-Migrate
├── tests/                    # (Recomendado) Pruebas unitarias y de integración
├── .env.example              # Ejemplo de variables de entorno
├── .gitignore
├── config.py                 # Configuraciones de la aplicación (Flask)
├── requirements.txt          # Dependencias de Python
├── run.py                    # Punto de entrada para ejecutar la app localmente y comandos CLI
├── README.md                 # Este archivo
└── _routes.json              # Configuración de enrutamiento para Cloudflare Pages Functions
```

## Configuración y Ejecución Local

1.  **Clonar el repositorio:**
    ```bash
    git clone <url-del-repositorio>
    cd <nombre-del-repositorio>
    ```

2.  **Crear un entorno virtual e instalar dependencias:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Linux/macOS
    # venv\Scripts\activate    # En Windows
    pip install -r requirements.txt
    ```

3.  **Configurar variables de entorno:**
    *   Copiar `.env.example` a `.env` y modificarlo.
    *   Variables clave:
        *   `SECRET_KEY`: Clave secreta fuerte para Flask.
        *   `FLASK_APP=run.py`
        *   `FLASK_CONFIG=development` (o `production`)
        *   `DATABASE_URL` (opcional, por defecto usa `sqlite:///instance/app.db`)
        *   `ADMIN_EMAIL` (email para el primer administrador)
        *   `ADMIN_PASSWORD` (contraseña para el primer administrador)

4.  **Inicializar la base de datos y crear el usuario administrador:**
    ```bash
    export FLASK_APP=run.py        # (o `set FLASK_APP=run.py` en Windows)
    export FLASK_CONFIG=development # (o `set FLASK_CONFIG=development`)
    flask init-db
    flask create-admin
    ```
    Esto creará las tablas de la base de datos, los roles y permisos por defecto, y el usuario administrador especificado en `config.py` o variables de entorno.

5.  **Ejecutar la aplicación localmente:**
    ```bash
    flask run
    ```
    La aplicación estará disponible en `http://127.0.0.1:5000`.

## Despliegue en Cloudflare Pages

Esta aplicación está estructurada para ser desplegable en Cloudflare Pages utilizando Funciones Python para el backend, Cloudflare D1 para la base de datos, y Cloudflare R2 para el almacenamiento de archivos (como imágenes subidas).

Para una guía detallada paso a paso sobre el despliegue, consulta el archivo:
**[Guía Detallada de Despliegue en Cloudflare Pages](DEPLOY_CLOUDFLARE.md)**

A continuación, se resumen los puntos clave y consideraciones:

1.  **Servicios de Cloudflare Necesarios:**
    *   **Cloudflare Pages:** Para el hosting del frontend y la ejecución de las Funciones Python.
    *   **Cloudflare D1:** Como base de datos SQL (el esquema debe crearse manualmente).
    *   **Cloudflare R2:** Para el almacenamiento de archivos subidos (ej. imágenes de formularios).

2.  **Configuración del Proyecto en Pages:**
    *   Conectar el repositorio Git.
    *   Establecer un comando de build (ej. `pip install -r requirements.txt && mkdir -p static_root && cp -r app/static/* static_root/`).
    *   Configurar el directorio de salida (generalmente la raíz del proyecto).
    *   Definir variables de entorno para la configuración de Flask, credenciales de R2 (si se usa `boto3`), y la clave secreta.

3.  **Bindings de Funciones:**
    *   Configurar bindings en Pages para D1 (ej. `DB`) y R2 (ej. `MY_R2_BUCKET`) para permitir que las Funciones Python accedan a estos servicios de forma segura.

4.  **Adaptador WSGI:**
    *   El archivo `functions/[[path]].py` actúa como el handler. Se necesita un adaptador WSGI para que las solicitudes de Cloudflare Functions sean procesadas por la aplicación Flask. La implementación de este adaptador es crucial y depende de las recomendaciones de Cloudflare para Python.

5.  **Enrutamiento y Archivos Estáticos:**
    *   El archivo `_routes.json` gestiona qué solicitudes van a las Funciones y cuáles sirven archivos estáticos.
    *   Los archivos estáticos de la aplicación (CSS, JS) deben ser copiados a una ubicación accesible por Cloudflare Pages durante el build (ej. una carpeta `static_root`) y la aplicación Flask configurada para usar esta ruta.

6.  **Inicialización de Datos en D1:**
    *   El esquema de la base de datos D1 debe crearse manualmente (ej. usando `wrangler d1 execute`).
    *   Los datos iniciales (roles, permisos, usuario admin) deben insertarse en D1, ya sea mediante `wrangler` o un endpoint temporal protegido en la aplicación.

## Consideraciones Adicionales

*   **Seguridad:**
    *   **NUNCA** cometer claves secretas o contraseñas directamente en el código. Usar variables de entorno.
    *   Revisar y fortalecer las políticas de CSRF, CSP y otras cabeceras de seguridad según sea necesario.
*   **Migraciones de Base de Datos con D1:** Si se realizan cambios en el esquema de `models.py` después del despliegue inicial, se necesitará un proceso para migrar el esquema de la base de datos D1. `Flask-Migrate` (Alembic) no funciona directamente con D1 sin un dialecto de SQLAlchemy específico para D1. Las migraciones podrían necesitar ser manuales (SQL) o mediante herramientas que soporten D1.
*   **Adaptador WSGI para Cloudflare:** La parte más crítica para el despliegue en Cloudflare Functions es el adaptador WSGI. Se recomienda buscar la documentación más reciente de Cloudflare o ejemplos comunitarios para una implementación robusta.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o un Pull Request.
