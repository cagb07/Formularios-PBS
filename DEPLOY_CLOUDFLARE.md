# Guía Detallada de Despliegue: Aplicación Flask en Cloudflare Pages con D1 y R2

Esta guía profundiza en los pasos para desplegar la aplicación Flask en Cloudflare Pages, utilizando Cloudflare D1 para la base de datos y Cloudflare R2 para el almacenamiento de archivos.

**Paso 0: Preparativos en Cloudflare**

1.  **Crear Base de Datos D1:**
    *   Navega a tu panel de control de Cloudflare -> Workers & Pages -> D1.
    *   Crea una nueva base de datos. Anota el "Database ID" (o nombre) y el "Account ID".
    *   **Ejecutar Esquema SQL:** El esquema de la base de datos debe crearse manualmente en D1.
        *   Localmente, después de ejecutar `flask init-db` (que crea `instance/app.db` si usas SQLite), puedes volcar el esquema:
            ```bash
            sqlite3 instance/app.db .schema > schema.sql
            ```
        *   Luego, ejecuta este archivo `schema.sql` contra tu base de datos D1 usando Wrangler CLI (necesitarás Node.js y npm/npx):
            ```bash
            npx wrangler d1 execute <NOMBRE_TU_DB_D1> --file=./schema.sql
            ```
            (Reemplaza `<NOMBRE_TU_DB_D1>` con el nombre de tu base de datos D1).
        *   **Nota Importante:** `flask init-db` (que usa SQLAlchemy `db.create_all()`) no creará tablas en D1 directamente desde la aplicación en ejecución. El esquema debe preexistir en D1.

2.  **Crear Bucket R2 y Configurar Acceso:**
    *   Navega a tu panel de control de Cloudflare -> R2.
    *   Crea un nuevo bucket. Anota el nombre exacto del bucket.
    *   **Acceso Público (Opcional pero Recomendado para Imágenes de Formularios):** Decide si los archivos subidos serán de acceso público.
        *   Si es así, en la configuración del bucket R2 (Settings -> Public access), conecta un dominio o subdominio y permite el acceso público (ej., `https://img.tudominio.com` o usa la URL pública proporcionada por R2 como `https://pub-<ID_BUCKET_HEX>.r2.dev`). Anota esta URL base pública, ya que la necesitarás para la variable `R2_PUBLIC_URL_BASE`.
        *   Si los archivos no son públicos, la aplicación necesitaría generar URLs firmadas para el acceso, lo cual añade complejidad y no está implementado en la versión actual de la aplicación.
    *   **Credenciales de API para R2 (necesarias si usas `boto3` con credenciales explícitas en lugar de bindings de funciones directamente para la subida):**
        *   En el panel de R2, haz clic en "Manage R2 API Tokens" (o desde "My Profile" -> "API Tokens" -> "Create Token" con la plantilla "Edit R2" o permisos personalizados de lectura/escritura para R2).
        *   Crea un token. Anota de forma segura el "Access Key ID" y el "Secret Access Key".
        *   También necesitarás tu "Account ID" de Cloudflare (visible en la URL del panel de R2 o en la información general de la cuenta).

**Paso 1: Configurar el Proyecto en Cloudflare Pages**

1.  **Crear Nuevo Proyecto en Pages:**
    *   En el panel de control de Cloudflare, ve a Workers & Pages -> Pages -> "Create a project".
    *   Conecta tu proveedor Git (GitHub, GitLab) y selecciona el repositorio de la aplicación.

2.  **Configuración de Build y Despliegue:**
    *   **Project Name:** Elige un nombre para tu proyecto (ej., `mi-plataforma-formularios`).
    *   **Production Branch:** Selecciona la rama principal de tu repositorio (ej., `main` o `master`).
    *   **Framework Preset:** Selecciona `None`.
    *   **Build Settings:**
        *   **Build command:**
            ```bash
            pip install -r requirements.txt && mkdir -p static_root && cp -r app/static/* static_root/
            ```
            (Este comando instala las dependencias de Python y luego copia los archivos estáticos de `app/static` a una carpeta `static_root` en la raíz del directorio de build. El nombre `static_root` es un ejemplo, puedes usar `public/static` u otro, pero debe coincidir con la configuración de Flask y `_routes.json`).
        *   **Build output directory:** `/` (la raíz del repositorio). Esto es importante porque `functions` y `_routes.json` deben estar en la raíz del directorio que Pages despliega. La carpeta `static_root` también se creará aquí.
        *   **Root directory (avanzado):** `/` (si tu `requirements.txt` y el resto del código fuente están en la raíz del repositorio).

3.  **Configurar Variables de Entorno (Secrets y Texto Plano):**
    *   Ve a la configuración de tu proyecto en Pages -> Settings -> Environment variables.
    *   **Variables de Producción (y Previsualización si es necesario):**
        *   `SECRET_KEY`: (Secret) Tu clave secreta de Flask, debe ser larga y aleatoria.
        *   `FLASK_CONFIG_CLOUDFLARE`: (Texto plano) `production` (o el nombre de la configuración que uses para Cloudflare, ej. `ProductionConfig` en `config.py`).
        *   `ADMIN_EMAIL`: (Texto plano) Email para el administrador por defecto que se creará.
        *   `ADMIN_PASSWORD`: (Secret) Contraseña para el administrador por defecto.
        *   **Para R2 (si se usa `boto3` con credenciales, como se esbozó en `config.py`):**
            *   `R2_BUCKET_NAME`: (Texto plano) El nombre de tu bucket R2.
            *   `R2_ACCOUNT_ID`: (Texto plano) Tu Cloudflare Account ID.
            *   `R2_ACCESS_KEY_ID`: (Secret) El Access Key ID para el token de API de R2.
            *   `R2_SECRET_ACCESS_KEY`: (Secret) El Secret Access Key para el token de API de R2.
            *   `R2_PUBLIC_URL_BASE`: (Texto plano) La URL base pública de tu bucket R2 (ej., `https://pub-xxxxxxxx.r2.dev/nombre-bucket` o tu dominio personalizado configurado para el bucket).
        *   **Nota sobre `D1_DATABASE_URL`:** Esta variable de entorno, como se definió en `config.py`, no se usa directamente si se utilizan *bindings* de D1. El binding en sí mismo proporciona el acceso a la base de datos dentro del contexto de la función. Si optas por conectarte a D1 a través de su API HTTP con un token (menos común para funciones), entonces necesitarías configurar esas credenciales.

4.  **Guardar y Desplegar:**
    *   Haz clic en "Save and Deploy". Cloudflare Pages intentará construir y desplegar tu sitio.
    *   Monitorea los logs del build para cualquier error (especialmente con `pip install` o los comandos de copia de archivos).

**Paso 2: Configurar Bindings para Funciones (D1 y R2)**

Los bindings permiten a tus Funciones de Pages (el código Python en `functions/[[path]].py`) acceder a recursos de Cloudflare como D1 y R2 de forma segura y optimizada.

1.  **Binding para D1:**
    *   Ve a la configuración de tu proyecto en Pages -> Settings -> Functions -> "D1 database bindings".
    *   Haz clic en "Add binding".
    *   **Variable name:** `DB` (Este será el nombre del objeto en `context.env.DB` dentro de tu función Python, que te permitirá interactuar con D1).
    *   **D1 Database:** Selecciona la base de datos D1 que creaste en el Paso 0.1.
    *   **Interacción con D1 desde Flask/SQLAlchemy:**
        *   **Desafío Principal:** SQLAlchemy no soporta D1 de forma nativa con un simple string de conexión como lo hace con PostgreSQL o MySQL. D1 tiene una API similar a SQLite pero se accede a través de un cliente específico proporcionado por el entorno de Cloudflare (el objeto `context.env.DB`).
        *   **Alternativas:**
            1.  **Usar un Cliente Python para D1 Directamente:** Para las operaciones de base de datos dentro de las rutas de Flask cuando la app se ejecuta en Cloudflare, tendrías que usar el cliente D1 (accesible a través de `context.env.DB`) en lugar de los métodos de SQLAlchemy (`User.query`, `db.session.add`, etc.). Esto implicaría reescribir significativamente la lógica de acceso a datos o crear una capa de abstracción.
            2.  **Conectarse a una Base de Datos como Servicio (DBaaS) Estándar:** Esta es a menudo la ruta más sencilla para aplicaciones Flask/SQLAlchemy existentes. Utiliza una base de datos hosteada compatible con SQLAlchemy (ej., PostgreSQL en Neon, Supabase, Aiven; MySQL en PlanetScale). Configura `SQLALCHEMY_DATABASE_URI` en tus variables de entorno de Pages con el string de conexión de esta DBaaS. En este caso, no necesitarías el binding D1.
        *   Si decides proceder con D1 y SQLAlchemy, necesitarías investigar sobre posibles dialectos de SQLAlchemy para D1 o adaptadores comunitarios, o estar preparado para una integración más manual.

2.  **Binding para R2:**
    *   Ve a la configuración de tu proyecto en Pages -> Settings -> Functions -> "R2 bucket bindings".
    *   Haz clic en "Add binding".
    *   **Variable name:** `MY_R2_BUCKET` (Este será `context.env.MY_R2_BUCKET` en tu código de función).
    *   **R2 Bucket:** Selecciona tu bucket R2 creado en el Paso 0.2.
    *   **Adaptar Código de Subida:** La lógica de subida de archivos en `app/forms_management/routes.py` debería idealmente usar este binding `context.env.MY_R2_BUCKET.put(...)` para subir archivos. Esto es generalmente más seguro y fácil de gestionar que manejar credenciales de `boto3` directamente en la función, aunque `boto3` con las variables de entorno también es una opción viable si el binding presenta limitaciones para tu caso de uso.

**Paso 3: Adaptador WSGI en `functions/[[path]].py`**

El archivo `functions/[[path]].py` es el handler que Cloudflare Pages ejecutará para las rutas dinámicas.

*   **Necesitas un Adaptador WSGI:** Para que Flask (una aplicación WSGI) funcione con el modelo de ejecución de Cloudflare Pages Functions para Python, se requiere un adaptador. El entorno de ejecución de Pages Functions pasa un objeto `context` a tu handler, y este `context` contiene la información de la solicitud HTTP. Esto necesita ser traducido al estándar WSGI que Flask espera.
*   **Opciones:**
    *   **Soporte Nativo/Librerías Recomendadas:** Verifica la documentación de Cloudflare Pages para Python. Es posible que Cloudflare ahora ofrezca una manera más directa de servir aplicaciones WSGI o recomiende bibliotecas específicas para la adaptación (similar a `mangum` para AWS Lambda o `vercel-wsgi` para Vercel).
    *   **Implementación Manual (Conceptual):** Si no hay un adaptador simple, tendrías que construir el entorno WSGI a partir del objeto `context.request` y luego llamar a `app.wsgi_app(environ, start_response)`. Esto es complejo.
    *   **Ejemplo Simplificado (si CF Pages busca `app`):** Algunas plataformas buscan una variable global llamada `app` que sea una instancia de aplicación WSGI. Si `functions/[[path]].py` simplemente contiene:
        ```python
        # functions/[[path]].py
        import os
        from app import create_app

        # Asegúrate que create_app() puede acceder a los bindings pasados por el contexto
        # si es necesario para configurar la base de datos o R2 en tiempo de inicialización.
        # Esto podría requerir modificar create_app o inicializar la app dentro de onRequest.
        app = create_app(os.getenv('FLASK_CONFIG_CLOUDFLARE') or 'production')

        # Si el runtime de Cloudflare Pages recoge 'app' automáticamente,
        # la función onRequest puede no ser estrictamente necesaria o se simplifica.
        ```
    *   **Si se Requiere un Handler `onRequest` Explícito:**
        ```python
        # functions/[[path]].py
        import os
        from app import create_app
        # from alguna_libreria_adaptadora_cf_wsgi import Adapter

        flask_app = create_app(os.getenv('FLASK_CONFIG_CLOUDFLARE') or 'production')
        # adapter = Adapter(flask_app) # Inicializar el adaptador

        # def onRequest(context):
        #     # Aquí el adaptador usaría flask_app y context (que tiene request, env, etc.)
        #     # return adapter.handle(context.request, context.env)
        #     # El retorno debe ser un objeto Response compatible con Cloudflare.
        #     # Este es un placeholder; el adaptador real es crucial.
        #     return Response("Adaptador WSGI para Flask necesita implementación.", status=501) # Necesitas importar o usar Response de CF
        ```
    La clave aquí es la documentación oficial de Cloudflare Pages para Python.

**Paso 4: Archivos Estáticos y Enrutamiento (`_routes.json`)**

1.  **`_routes.json`:**
    *   Coloca este archivo en la raíz de tu "Build output directory" (que es `/` según el comando de build sugerido).
    *   El contenido para dirigir todo lo no estático a tus funciones y servir estáticos directamente es:
        ```json
        {
          "version": 1,
          "include": ["/*"],
          "exclude": ["/static/*", "/favicon.ico"]
        }
        ```
2.  **Servir Estáticos:**
    *   Con el comando de build `... && mkdir -p static_root && cp -r app/static/* static_root/`, tus archivos estáticos de la aplicación (CSS, JS de UI) estarán en la carpeta `static_root/` en la raíz del despliegue.
    *   En `app/__init__.py`, al crear la aplicación Flask, asegúrate de que `static_folder` apunte a esta ubicación y `static_url_path` sea el correcto:
        ```python
        # En app/__init__.py dentro de create_app()
        app = Flask(__name__,
                    instance_relative_config=True,
                    static_folder='static_root',  # Nombre de la carpeta creada en el build
                    static_url_path='/static')   # URL base para los estáticos
        ```
    *   El `exclude: ["/static/*"]` en `_routes.json` hará que Cloudflare Pages sirva directamente cualquier archivo bajo la URL `/static/` desde la carpeta `static_root/` de tu build, sin pasar por la función Python.

**Paso 5: Inicialización de Datos (Admin y Roles en D1)**

Los comandos `flask init-db` y `flask create-admin` se ejecutan localmente pero no automáticamente en el entorno de Pages para poblar D1.

1.  **Esquema de D1:** Ya cubierto en el Paso 0.1 (creación manual del esquema).
2.  **Roles y Permisos:** La lógica de `Role.insert_roles()` (que es llamada por `flask init-db` localmente) necesita ejecutarse una vez contra D1 para insertar los datos iniciales de roles y permisos.
    *   **Opción 1 (Endpoint Temporal Protegido):** Crea una ruta temporal en tu aplicación Flask (ej. `/admin/setup-initial-data`), protegida adecuadamente (ej., con una clave secreta en la URL o requiriendo login de un admin que crearías manualmente primero). Esta ruta llamaría a `Role.insert_roles()`. Accede a esta ruta una vez después del primer despliegue exitoso. Luego, elimina o deshabilita esta ruta.
    *   **Opción 2 (Wrangler CLI):** Genera las sentencias SQL necesarias para insertar los roles (`roles` tabla) y permisos (`permissions` tabla), y sus relaciones (`role_permissions` tabla). Ejecútalas con `npx wrangler d1 execute <DB_NAME> --command="INSERT INTO ..."`.
3.  **Usuario Administrador:** Similarmente, para crear el primer usuario administrador:
    *   **Opción 1 (Endpoint Temporal):** Parte del mismo endpoint de setup.
    *   **Opción 2 (Wrangler CLI):**
        *   Obtén el hash de la contraseña deseada ejecutando localmente:
            ```python
            # En un shell de python local con tu app y bcrypt instalados:
            from werkzeug.security import generate_password_hash
            hashed_password = generate_password_hash("TuContraseñaAdminSegura123!")
            print(hashed_password)
            ```
        *   Luego, usa este hash en una sentencia `INSERT` para la tabla `users` en D1, y también inserta la relación en `user_roles` para asignarle el rol 'Admin'.

**Paso 6: Pruebas y Logs**

*   Después de cada despliegue (o cambio de configuración), prueba todas las funcionalidades clave de la aplicación desplegada.
*   Utiliza los logs de "Builds" y "Functions" en el panel de Cloudflare Pages para diagnosticar errores de build o de ejecución de tus funciones Python.

**Consideraciones Finales y Desafíos:**

*   **Cold Starts:** Las funciones serverless pueden experimentar "cold starts" (un retraso en la primera invocación después de un período de inactividad).
*   **Límites de Funciones:** Ten en cuenta los límites de tiempo de ejecución, memoria, tamaño del paquete, etc., de Cloudflare Pages Functions.
*   **Documentación Oficial de Cloudflare:** Es tu mejor amiga. La plataforma Cloudflare evoluciona rápidamente, así que siempre consulta la documentación oficial para las prácticas más recientes y precisas sobre el despliegue de aplicaciones Python/WSGI, el uso de bindings de D1/R2, y la configuración general de Pages Functions.
*   **Interacción ORM (SQLAlchemy) con D1:** Este sigue siendo el mayor desafío técnico si se desea mantener SQLAlchemy. Si la interacción directa con D1 a través de su cliente (proporcionado por el binding) es demasiado engorrosa de integrar en una base de código SQLAlchemy existente, considera seriamente usar una DBaaS tradicional que sea compatible con SQLAlchemy.

Este proceso de despliegue es avanzado y requiere una buena comprensión tanto de Flask como de los servicios de Cloudflare. ¡Mucha suerte!
