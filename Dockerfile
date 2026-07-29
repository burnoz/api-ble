# Imagen base
FROM python:3.11-slim

# Directorio de trabajo
WORKDIR /app

# Dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Exponer el puerto en el que la aplicación se ejecutará
EXPOSE 5000

# env
# Hace que los logs se muestren en tiempo real
ENV PYTHONUNBUFFERED=1
# Evita que Python cree archivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1

# Comando para ejecutar la api
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--chdir", "src", "api-leaves:app"]