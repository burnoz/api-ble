# api-leaves

API para aplicación de Cáritas de Monterrey (Equipo Leaves)

Este repositorio contiene el API REST del sistema de donaciones de Cáritas Monterrey, que permite gestionar donaciones, usuarios, bazares y fotografías de artículos donados.

## Características principales

- **Autenticación de usuarios** (donantes y administradores de bazar)
- **Gestión, consulta y creación de donaciones** con categorías múltiples y estados (pendiente, aprobado, entregado, rechazado)
- **Carga de imágenes** asociadas a donaciones
- **Información de bazares** para mapas interactivos
- **Historial completo** de donaciones por usuario y por bazar
- **Consultas parametrizadas** para prevenir SQL injection
- **Manejo seguro de archivos** para evitar directory traversal attacks

## Tecnologías

- Flask (Python web framework)
- PyMySQL (conexión a MySQL/MariaDB)
- Werkzeug (manejo seguro de archivos)
- python-dotenv (gestión de variables de entorno)
- Gunicorn (servidor WSGI para producción)

## Endpoints principales

### Usuarios

- `POST /usuario/auth` - Autenticación
- `POST /usuario/nuevo` - Registro de donante
- `GET /usuario/get/<id>` - Información de usuario
- `PUT /usuario/editar/<id>` - Actualizar perfil

### Donaciones

- `POST /donacion/nueva` - Crear donación con imágenes
- `GET /donacion/activas/<user_id>` - Donaciones pendientes/aprobadas
- `GET /donacion/historial_usuario/<user_id>` - Historial completo
- `GET /donacion/solicitudes/<bazar_id>` - Solicitudes pendientes de un bazar
- `GET /donacion/camino/<bazar_id>` - Donaciones aprobadas en camino
- `PUT /donacion/aceptar/<id>` - Aprobar donación
- `PUT /donacion/rechazar/<id>` - Rechazar donación
- `PUT /donacion/entregar/<id>` - Marcar como entregada

### Bazares

- `GET /bazar/mapa` - Información sobre bazares registrados

### Fotos

- `GET /foto/<filename>` - Servir imagen estática

## Configuración

Crear archivo `.env` en la raíz del proyecto:

```env
DB_HOST=ip
DB_USER=tu_usuario
DB_PASS=tu_contraseña
DB_NAME=caritas

UPLOAD_FOLDER=/home/user/fotos  # Linux
```

## Instalación y uso (Linux)

```powershell
# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar API
gunicorn --bind 0.0.0.0:5000 api-leaves:app &

# Detener API (# Ejecutar con precaución, ya que detiene todos los procesos gunicorn, buscar PID específico si es necesario)
pkill gunicorn
```