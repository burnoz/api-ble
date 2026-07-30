from flask import Flask, jsonify, request, send_from_directory
import pymysql
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv

load_dotenv()

# nyehehehe

categorias_map = {
    "Medicamentos no caducos": 1,
    "Artículos médicos": 2,
    "Muebles": 3,
    "Electrodomésticos": 4,
    "Ropa": 5,
    "Pañales": 6,
    "Otros": 7
}

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DB_HOST = os.getenv("DB_HOST")
DB_PORT = 3306
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

def get_conn():
	return pymysql.connect(
		host=DB_HOST,
		port=DB_PORT,
		user=DB_USER,
		password=DB_PASS,
		db=DB_NAME,
		cursorclass=pymysql.cursors.DictCursor,
		autocommit=True,
	)

def query(sql, params=None):
	conn = get_conn()
	try:
		with conn.cursor() as cur:
			cur.execute(sql, params or ())
			if cur.description:
				return cur.fetchall()
			return []
		
	finally:
		conn.close()


def execute(sql, params=None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            conn.commit()
    
    finally:
        conn.close()


@app.route('/')
def home():
    return jsonify({"message": "API Leaves"})


@app.route('/usuario/auth', methods=['POST'])
def auth_usuario():
    data = request.get_json()
    correo = data.get('correo')
    hashed_pswd = data.get('hashed_pswd')

    sql = """
    SELECT u.ID, u.Correo, u.Nombre, u.Telefono, u.Direccion, u.RolID,
           r.Descripcion AS Rol
    FROM Usuario u
    LEFT JOIN Rol r ON u.RolID = r.ID
    WHERE u.Correo = %s AND u.HashedPswd = %s
    """
    
    usuarios = query(sql, (correo, hashed_pswd))
    
    if usuarios:
        return jsonify(usuarios[0])
    
    return jsonify({"error": "Credenciales inválidas"}), 401


@app.route('/usuario/get/<int:user_id>', methods=['GET'])
def get_usuario(user_id):
    sql = """
    SELECT u.ID, u.Correo, u.HashedPswd, u.Nombre, u.Telefono, u.Direccion, u.RolID,
           r.Descripcion AS Rol
    FROM Usuario u
    LEFT JOIN Rol r ON u.RolID = r.ID
    WHERE u.ID = %s
    """
    
    usuarios = query(sql, (user_id,))
    
    if usuarios:
        return jsonify(usuarios[0])
    
    return jsonify({"error": "Usuario no encontrado"}), 404


@app.route('/usuario/nuevo', methods=['POST'])
def nuevo_usuario():
    data = request.get_json()
    correo = data.get('correo')
    hashed_pswd = data.get('hashed_pswd')
    nombre = data.get('nombre')
    telefono = data.get('telefono')
    direccion = data.get('direccion')
    rol_id = data.get('rol_id', 2)  # Siempre es 2 para un donador

    # Verificar que no exista ya un usuario con ese correo
    existe = query("SELECT ID FROM Usuario WHERE Correo = %s", (correo,))
    if existe:
        return jsonify({"error": "Ya existe una cuenta con ese correo"}), 409

    sql = """
    INSERT INTO Usuario (Correo, HashedPswd, Nombre, Telefono, Direccion, RolID)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    execute(sql, (correo, hashed_pswd, nombre, telefono, direccion, rol_id))
    
    return jsonify({"message": "Usuario creado"}), 201


@app.route('/usuario/editar/<int:user_id>', methods=['PUT'])
def editar_usuario(user_id):
    data = request.get_json()
    correo = data.get('correo')
    nombre = data.get('nombre')
    telefono = data.get('telefono')
    direccion = data.get('direccion')

    sql = """
    UPDATE Usuario
    SET Correo = %s, Nombre = %s, Telefono = %s, Direccion = %s
    WHERE ID = %s
    """
    
    execute(sql, (correo, nombre, telefono, direccion, user_id))
    
    return jsonify({"message": "Usuario actualizado"}), 200


@app.route('/donacion/activas/<int:user_id>', methods=['GET'])
def get_donaciones_activas(user_id):
    sql = """
    SELECT d.*, GROUP_CONCAT(c.Descripcion SEPARATOR ',') AS Categorias,
           bz.Nombre AS BazarNombre
    FROM Donacion d
    LEFT JOIN DonacionCategoria dc ON dc.FolioDonacion = d.Folio
    LEFT JOIN Categoria c ON c.ID = dc.CategoriaID
    LEFT JOIN Bazar bz ON d.BazarID = bz.ID
    WHERE d.UsuarioID = %s AND (d.EstadoDonativoID = 1 OR d.EstadoDonativoID = 2)
    GROUP BY d.Folio
    """
    
    donaciones = query(sql, (user_id,))
    
    for d in donaciones:
        cats = d.get('Categorias')
        d['Categorias'] = cats.split(',') if cats else []

        d['Bazar'] = {
            'ID': d.pop('BazarID', None),
            'Nombre': d.pop('BazarNombre', None)
        }
        
        fotos = query("SELECT Ruta FROM Foto WHERE Donacion = %s", (d.get('Folio'),))
        d['Fotos'] = [f['Ruta'] for f in fotos]
    
    return jsonify(donaciones)


@app.route('/donacion/historial_usuario/<int:user_id>', methods=['GET'])
def get_historial_usuario(user_id):
    sql = """
    SELECT d.*, GROUP_CONCAT(c.Descripcion SEPARATOR ',') AS Categorias,
           bz.Nombre AS BazarNombre
    FROM Donacion d
    LEFT JOIN DonacionCategoria dc ON dc.FolioDonacion = d.Folio
    LEFT JOIN Categoria c ON c.ID = dc.CategoriaID
    LEFT JOIN Bazar bz ON d.BazarID = bz.ID
    WHERE d.UsuarioID = %s AND (d.EstadoDonativoID = 3 OR d.EstadoDonativoID = 4 OR d.EstadoDonativoID = 5)
    GROUP BY d.Folio
    """
    
    donaciones = query(sql, (user_id,))
    
    for d in donaciones:
        cats = d.get('Categorias')
        d['Categorias'] = cats.split(',') if cats else []

        d['Bazar'] = {
            'ID': d.pop('BazarID', None),
            'Nombre': d.pop('BazarNombre', None)
        }

        fotos = query("SELECT Ruta FROM Foto WHERE Donacion = %s", (d.get('Folio'),))
        d['Fotos'] = [f['Ruta'] for f in fotos]
    
    return jsonify(donaciones)


@app.route('/donacion/historial_bazar/<int:bazar_id>', methods=['GET'])
def get_historial_bazar(bazar_id):
    sql = """
    SELECT d.*, GROUP_CONCAT(c.Descripcion SEPARATOR ',') AS Categorias,
           u.Nombre AS UsuarioNombre,
           bz.Nombre AS BazarNombre
    FROM Donacion d
    LEFT JOIN DonacionCategoria dc ON dc.FolioDonacion = d.Folio
    LEFT JOIN Categoria c ON c.ID = dc.CategoriaID
    LEFT JOIN Usuario u ON d.UsuarioID = u.ID
    LEFT JOIN Bazar bz ON d.BazarID = bz.ID
    WHERE d.BazarID = %s AND (d.EstadoDonativoID = 3 OR d.EstadoDonativoID = 4 OR d.EstadoDonativoID = 5)
    GROUP BY d.Folio
    """
    
    donaciones = query(sql, (bazar_id,))
    
    for d in donaciones:
        cats = d.get('Categorias')
        d['Categorias'] = cats.split(',') if cats else []
        usuario_nombre = d.pop('UsuarioNombre', None)
        d['Usuario'] = {'Nombre': usuario_nombre}

        d['Bazar'] = {
            'ID': d.pop('BazarID', None),
            'Nombre': d.pop('BazarNombre', None)
        }

        fotos = query("SELECT Ruta FROM Foto WHERE Donacion = %s", (d.get('Folio'),))
        d['Fotos'] = [f['Ruta'] for f in fotos]
    
    return jsonify(donaciones)


@app.route('/donacion/camino/<int:bazar_id>', methods=['GET'])
def get_camino_bazar(bazar_id):
    sql = """
    SELECT d.*, GROUP_CONCAT(c.Descripcion SEPARATOR ',') AS Categorias,
           u.Nombre AS UsuarioNombre,
           bz.Nombre AS BazarNombre
    FROM Donacion d
    LEFT JOIN DonacionCategoria dc ON dc.FolioDonacion = d.Folio
    LEFT JOIN Categoria c ON c.ID = dc.CategoriaID
    LEFT JOIN Usuario u ON d.UsuarioID = u.ID
    LEFT JOIN Bazar bz ON d.BazarID = bz.ID
    WHERE d.BazarID = %s AND (d.EstadoDonativoID = 2)
    GROUP BY d.Folio
    """
    
    donaciones = query(sql, (bazar_id,))
    
    for d in donaciones:
        cats = d.get('Categorias')
        d['Categorias'] = cats.split(',') if cats else []
        usuario_nombre = d.pop('UsuarioNombre', None)
        d['Usuario'] = {'Nombre': usuario_nombre}

        d['Bazar'] = {
            'ID': d.pop('BazarID', None),
            'Nombre': d.pop('BazarNombre', None)
        }

        fotos = query("SELECT Ruta FROM Foto WHERE Donacion = %s", (d.get('Folio'),))
        d['Fotos'] = [f['Ruta'] for f in fotos]

    return jsonify(donaciones)


@app.route('/donacion/solicitudes/<int:bazar_id>', methods=['GET'])
def get_solicitudes_bazar(bazar_id):
    sql = """
    SELECT d.*, GROUP_CONCAT(c.Descripcion SEPARATOR ',') AS Categorias,
           u.Nombre AS UsuarioNombre,
           bz.Nombre AS BazarNombre
    FROM Donacion d
    LEFT JOIN DonacionCategoria dc ON dc.FolioDonacion = d.Folio
    LEFT JOIN Categoria c ON c.ID = dc.CategoriaID
    LEFT JOIN Usuario u ON d.UsuarioID = u.ID
    LEFT JOIN Bazar bz ON d.BazarID = bz.ID
    WHERE d.BazarID = %s AND (d.EstadoDonativoID = 1)
    GROUP BY d.Folio
    """
    
    donaciones = query(sql, (bazar_id,))
    
    for d in donaciones:
        cats = d.get('Categorias')
        d['Categorias'] = cats.split(',') if cats else []
        usuario_nombre = d.pop('UsuarioNombre', None)
        d['Usuario'] = {'Nombre': usuario_nombre}

        d['Bazar'] = {
            'ID': d.pop('BazarID', None),
            'Nombre': d.pop('BazarNombre', None)
        }

        fotos = query("SELECT Ruta FROM Foto WHERE Donacion = %s", (d.get('Folio'),))
        d['Fotos'] = [f['Ruta'] for f in fotos]
    
    return jsonify(donaciones)


@app.route('/donacion/nueva', methods=['POST'])
def nueva_donacion_imagen():
    usuario_id = request.form.get('usuario_id')
    bazar_id = request.form.get('bazar_id')
    descripcion = request.form.get('descripcion')
    categorias = request.form.getlist('categorias') # Recibe un string list
    cats = []

    for cat in categorias:
        cat_id = categorias_map.get(cat)
        
        print(f"Categoría: {cat}, ID: {cat_id}")

        if cat_id:
            cats.append(cat_id)

    sql_donacion = """
    INSERT INTO Donacion (UsuarioID, BazarID, EstadoDonativoID, FechaCreacion, FechaEntrega, Descripcion)
    VALUES (%s, %s, %s, NOW(), NULL, %s)
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql_donacion, (usuario_id, bazar_id, 1, descripcion))
            folio_donacion = cur.lastrowid

            sql_categoria = """
            INSERT INTO DonacionCategoria (FolioDonacion, CategoriaID)
            VALUES (%s, %s)
            """
            for cat_id in cats:
                cur.execute(sql_categoria, (folio_donacion, cat_id))

            if 'fotos' in request.files:
                fotos = request.files.getlist('fotos')
                sql_foto = "INSERT INTO Foto (Donacion, Ruta) VALUES (%s, %s)"
                
                for foto in fotos:
                    filename = secure_filename(foto.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    foto.save(file_path)
                    cur.execute(sql_foto, (folio_donacion, filename))
        
        conn.commit()
    
    finally:
        conn.close()

    return jsonify({"message": "Donación creada con imágenes", "folio": folio_donacion}), 201


@app.route('/foto/<filename>', methods=['GET'])
def get_photo(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/donacion/borrar/<int:donacion_id>', methods=['DELETE'])
def borrar_donacion(donacion_id):
    sql_borrar_categoria = "DELETE FROM DonacionCategoria WHERE FolioDonacion = %s"
    sql_borrar_donacion = "DELETE FROM Donacion WHERE Folio = %s"

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql_borrar_categoria, (donacion_id,))
            cur.execute(sql_borrar_donacion, (donacion_id,))
        conn.commit()
    
    finally:
        conn.close()

    return jsonify({"message": "Donación borrada"}), 200


@app.route('/donacion/aceptar/<int:donacion_id>', methods=['PUT'])
def aceptar_donacion(donacion_id):
    sql = """
    UPDATE Donacion
    SET EstadoDonativoID = 2, FechaEntrega = NOW()
    WHERE Folio = %s
    """
    
    execute(sql, (donacion_id,))
    
    return jsonify({"message": "Donación aceptada"}), 200


@app.route('/donacion/rechazar/<int:donacion_id>', methods=['PUT'])
def rechazar_donacion(donacion_id):
    sql = """
    UPDATE Donacion
    SET EstadoDonativoID = 4
    WHERE Folio = %s
    """
    
    execute(sql, (donacion_id,))
    
    return jsonify({"message": "Donación rechazada"}), 200


@app.route('/donacion/entregar/<int:donacion_id>', methods=['PUT'])
def entregar_donacion(donacion_id):
    sql = """
    UPDATE Donacion
    SET EstadoDonativoID = 3
    WHERE Folio = %s
    """

    execute(sql, (donacion_id,))
    
    return jsonify({"message": "Donación entregada"}), 200


@app.route('/bazar/mapa', methods=['GET'])
def get_bazares():
    sql = """
    SELECT b.ID, b.Nombre, b.DireccionBazar, b.Latitud, b.Longitud, u.Telefono
    FROM Bazar b
    INNER JOIN Usuario u ON b.AdminBazarID = u.ID
    WHERE b.Latitud IS NOT NULL AND b.Longitud IS NOT NULL
    """
    bazares = query(sql)
    return jsonify(bazares)


# Quitar para usar en el servidor
# if __name__ == '__main__':
#	app.run(host='0.0.0.0', port=5000)
