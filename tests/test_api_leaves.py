import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import importlib
import json
import tempfile
from io import BytesIO

# Add src to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the module with hyphen name
api_leaves = importlib.import_module("api-leaves")

class TestApiLeaves(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for file uploads
        self.temp_dir = tempfile.TemporaryDirectory()
        api_leaves.app.config['TESTING'] = True
        api_leaves.app.config['UPLOAD_FOLDER'] = self.temp_dir.name
        self.client = api_leaves.app.test_client()

    def tearDown(self):
        # Cleanup temporary directory
        self.temp_dir.cleanup()

    def test_home(self):
        """Test the home route returns the expected JSON."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data, {"message": "API Leaves"})

    @patch.object(api_leaves, 'query')
    def test_auth_usuario_success(self, mock_query):
        """Test successful user authentication."""
        mock_query.return_value = [{
            "ID": 1,
            "Correo": "test@example.com",
            "Nombre": "Test User",
            "Telefono": "12345678",
            "Direccion": "Calle Falsa 123",
            "RolID": 2,
            "Rol": "Donador"
        }]
        
        payload = {
            "correo": "test@example.com",
            "hashed_pswd": "hashedpassword123"
        }
        response = self.client.post('/usuario/auth', 
                                    data=json.dumps(payload),
                                    content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["Correo"], "test@example.com")
        self.assertEqual(data["Nombre"], "Test User")
        mock_query.assert_called_once()

    @patch.object(api_leaves, 'query')
    def test_auth_usuario_invalid_credentials(self, mock_query):
        """Test authentication fails with invalid credentials."""
        mock_query.return_value = []
        
        payload = {
            "correo": "wrong@example.com",
            "hashed_pswd": "wrongpassword"
        }
        response = self.client.post('/usuario/auth', 
                                    data=json.dumps(payload),
                                    content_type='application/json')
        
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertEqual(data, {"error": "Credenciales inválidas"})

    @patch.object(api_leaves, 'query')
    def test_get_usuario_found(self, mock_query):
        """Test getting an existing user."""
        mock_query.return_value = [{
            "ID": 1,
            "Correo": "test@example.com",
            "Nombre": "Test User",
            "Telefono": "12345678",
            "Direccion": "Calle Falsa 123",
            "RolID": 2,
            "Rol": "Donador"
        }]
        
        response = self.client.get('/usuario/get/1')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["ID"], 1)
        self.assertEqual(data["Nombre"], "Test User")

    @patch.object(api_leaves, 'query')
    def test_get_usuario_not_found(self, mock_query):
        """Test getting a non-existent user."""
        mock_query.return_value = []
        
        response = self.client.get('/usuario/get/999')
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertEqual(data, {"error": "Usuario no encontrado"})

    @patch.object(api_leaves, 'execute')
    @patch.object(api_leaves, 'query')
    def test_nuevo_usuario_success(self, mock_query, mock_execute):
        """Test successful registration of a new user."""
        # Mock query checking if email already exists: return empty (no duplicate)
        mock_query.return_value = []
        
        payload = {
            "correo": "new@example.com",
            "hashed_pswd": "newpassword123",
            "nombre": "New User",
            "telefono": "98765432",
            "direccion": "Avenida Siempre Viva 742"
        }
        
        response = self.client.post('/usuario/nuevo',
                                    data=json.dumps(payload),
                                    content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data, {"message": "Usuario creado"})
        mock_execute.assert_called_once()

    @patch.object(api_leaves, 'query')
    def test_nuevo_usuario_conflict(self, mock_query):
        """Test registration fails if user email already exists."""
        mock_query.return_value = [{"ID": 1}]
        
        payload = {
            "correo": "existing@example.com",
            "hashed_pswd": "password",
            "nombre": "Existing User"
        }
        
        response = self.client.post('/usuario/nuevo',
                                    data=json.dumps(payload),
                                    content_type='application/json')
        
        self.assertEqual(response.status_code, 409)
        data = response.get_json()
        self.assertEqual(data, {"error": "Ya existe una cuenta con ese correo"})

    @patch.object(api_leaves, 'execute')
    def test_editar_usuario(self, mock_execute):
        """Test updating user details."""
        payload = {
            "correo": "updated@example.com",
            "nombre": "Updated Name",
            "telefono": "55555555",
            "direccion": "Updated Address"
        }
        
        response = self.client.put('/usuario/editar/1',
                                   data=json.dumps(payload),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data, {"message": "Usuario actualizado"})
        mock_execute.assert_called_once()

    @patch.object(api_leaves, 'query')
    def test_get_donaciones_activas(self, mock_query):
        """Test getting active donations for a user."""
        # Side effect to handle multiple calls in query
        mock_query.side_effect = [
            [
                {
                    "Folio": 10,
                    "UsuarioID": 1,
                    "BazarID": 2,
                    "BazarNombre": "Bazar del Sol",
                    "EstadoDonativoID": 1,
                    "Categorias": "Medicamentos no caducos,Artículos médicos"
                }
            ],
            [
                {"Ruta": "foto1.jpg"},
                {"Ruta": "foto2.jpg"}
            ]
        ]
        
        response = self.client.get('/donacion/activas/1')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["Folio"], 10)
        self.assertEqual(data[0]["Categorias"], ["Medicamentos no caducos", "Artículos médicos"])
        self.assertEqual(data[0]["Bazar"], {"ID": 2, "Nombre": "Bazar del Sol"})
        self.assertEqual(data[0]["Fotos"], ["foto1.jpg", "foto2.jpg"])

    @patch.object(api_leaves, 'get_conn')
    def test_nueva_donacion_success(self, mock_get_conn):
        """Test creating a new donation with mock connection and cursor."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        mock_cursor.lastrowid = 123
        
        data = {
            'usuario_id': '1',
            'bazar_id': '2',
            'descripcion': 'Donación de prueba',
            'categorias': ['Medicamentos no caducos', 'Artículos médicos'],
            'fotos': (BytesIO(b'dummy file data'), 'donacion.jpg')
        }
        
        response = self.client.post('/donacion/nueva',
                                    data=data,
                                    content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 201)
        res_data = response.get_json()
        self.assertEqual(res_data["message"], "Donación creada con imágenes")
        self.assertEqual(res_data["folio"], 123)
        
        # Verify file was created in temporary upload folder
        uploaded_file_path = os.path.join(self.temp_dir.name, 'donacion.jpg')
        self.assertTrue(os.path.exists(uploaded_file_path))
        with open(uploaded_file_path, 'rb') as f:
            self.assertEqual(f.read(), b'dummy file data')

    @patch.object(api_leaves, 'get_conn')
    def test_borrar_donacion(self, mock_get_conn):
        """Test deleting a donation."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        response = self.client.delete('/donacion/borrar/10')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data, {"message": "Donación borrada"})
        
        # Check database cursor executions
        self.assertEqual(mock_cursor.execute.call_count, 2)

    @patch.object(api_leaves, 'execute')
    def test_aceptar_donacion(self, mock_execute):
        """Test accepting a donation."""
        response = self.client.put('/donacion/aceptar/10')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data, {"message": "Donación aceptada"})
        mock_execute.assert_called_once()

    @patch.object(api_leaves, 'query')
    def test_get_bazares(self, mock_query):
        """Test getting bazares map coordinates."""
        mock_query.return_value = [
            {
                "ID": 1,
                "Nombre": "Bazar Centro",
                "DireccionBazar": "Centro 123",
                "Latitud": 19.4326,
                "Longitud": -99.1332,
                "Telefono": "12345678"
            }
        ]
        
        response = self.client.get('/bazar/mapa')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["Nombre"], "Bazar Centro")

if __name__ == '__main__':
    unittest.main()
