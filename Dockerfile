# ============================================================================
# RUTA: backend/Dockerfile - VERSION CORRECTA
# DESCRIPCIÓN: Docker para FastAPI + Uvicorn
# USO: docker build -t fresst-bot . && docker run -p 8000:8000 fresst-bot
# ============================================================================

FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos
COPY . /app

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer puerto
EXPOSE 8000

# Variables de entorno (se sobreescriben con .env en producción)
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Comando de inicio CORRECTO
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
