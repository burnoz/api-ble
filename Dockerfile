# Imagen base
FROM python:3.11-slim

# Directorio de trabajo
WORKDIR /app

# Dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Exponer el puerto en el que la aplicación se ejecutará (Cloud Run usa 8080 por defecto)
EXPOSE 8080

# env
# Hace que los logs se muestren en tiempo real
ENV PYTHONUNBUFFERED=1
# Evita que Python cree archivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1

# Comando para ejecutar la api escuchando en el puerto configurado por la variable de entorno PORT (con fallback a 8080)
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8080} --chdir src api-leaves:app"]