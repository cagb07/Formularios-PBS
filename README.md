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

Esta aplicación está estructurada para ser desplegada en Cloudflare Pages con las siguientes consideraciones:

1.  **Fuente de Datos (Cloudflare D1):**
    *   La aplicación está configurada para usar Cloudflare D1 si se proporciona la variable de entorno `D1_DATABASE_URL`.
    *   Deberás crear una base de datos D1 en tu panel de Cloudflare y obtener su URL de conexión (o binding).
    *   Las migraciones de esquema iniciales (creación de tablas) se deben realizar contra D1 (ej. usando `wrangler d1 execute`). Los comandos `flask init-db` están pensados para SQLAlchemy y podrían necesitar adaptarse o ejecutarse en un entorno que pueda conectar a D1 con las herramientas adecuadas si el driver SQLAlchemy para D1 no es directo.

2.  **Almacenamiento de Archivos (Cloudflare R2):**
    *   Para la subida de imágenes, la aplicación está diseñada para usar Cloudflare R2 si se configuran las variables de entorno correspondientes (`R2_BUCKET_NAME`, `R2_ACCOUNT_ID`, etc.).
    *   Deberás crear un bucket R2 y configurar sus permisos (ej. para acceso público a los objetos si es necesario).
    *   Si R2 no está configurado, la aplicación intentará usar el directorio local `app/static/uploads/` (esto **no funcionará** correctamente en el entorno serverless de Cloudflare Pages para persistencia).

3.  **Configuración en Cloudflare Pages:**
    *   Conecta tu repositorio Git a Cloudflare Pages.
    *   **Configuración de Build:**
        *   Framework Preset: `None` (o `Python` si está disponible y es adecuado).
        *   Build command: `pip install -r requirements.txt && # (opcional) Comandos para mover estáticos si es necesario`
        *   Build output directory: `/` (la raíz del repositorio, o donde estén `_routes.json` y `functions/`).
        *   Root directory: `/` (o donde esté el `requirements.txt`).
    *   **Variables de Entorno:** Configura todas las variables necesarias en el panel de Cloudflare Pages (Secrets para `SECRET_KEY`, `ADMIN_PASSWORD`, credenciales de R2, etc., y variables planas para `FLASK_CONFIG_CLOUDFLARE='production'`, `ADMIN_EMAIL`, `D1_DATABASE_URL`, `R2_BUCKET_NAME`, etc.).
    *   **Compatibilidad de Funciones:** Asegúrate de que la compatibilidad con `python` esté habilitada para las funciones si es necesario.

4.  **Handler de Funciones (`functions/[[path]].py`):**
    *   Este archivo está destinado a ser el punto de entrada para las solicitudes dinámicas. Requiere un adaptador WSGI adecuado para conectar las solicitudes de Cloudflare Functions con la aplicación Flask. La implementación actual en `functions/[[path]].py` es un placeholder y necesitará ser completada con un adaptador funcional o según las directrices de Cloudflare para servir aplicaciones WSGI Python.

5.  **Enrutamiento (`_routes.json`):**
    *   El archivo `_routes.json` en la raíz del directorio de publicación define qué rutas son manejadas por las Funciones (`[[path]].py`) y cuáles son servidas como activos estáticos. Asegúrate de que la carpeta `static` de la aplicación sea servida correctamente.

## Consideraciones Adicionales

*   **Seguridad:**
    *   **NUNCA** cometer claves secretas o contraseñas directamente en el código. Usar variables de entorno.
    *   Revisar y fortalecer las políticas de CSRF, CSP y otras cabeceras de seguridad según sea necesario.
*   **Migraciones de Base de Datos con D1:** Si se realizan cambios en el esquema de `models.py` después del despliegue inicial, se necesitará un proceso para migrar el esquema de la base de datos D1. `Flask-Migrate` (Alembic) no funciona directamente con D1 sin un dialecto de SQLAlchemy específico para D1. Las migraciones podrían necesitar ser manuales (SQL) o mediante herramientas que soporten D1.
*   **Adaptador WSGI para Cloudflare:** La parte más crítica para el despliegue en Cloudflare Functions es el adaptador WSGI. Se recomienda buscar la documentación más reciente de Cloudflare o ejemplos comunitarios para una implementación robusta.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o un Pull Request.
