# ============================================================================
# RUTA: backend/main.py
# DESCRIPCIÓN: Aplicación FastAPI Principal
# USO: python main.py (ejecutar el servidor)
# ============================================================================

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Conectar a MongoDB
from config.database import connect_mongodb, close_mongodb

try:
    connect_mongodb()
except Exception as e:
    logger.error(f"❌ No se pudo conectar a MongoDB: {e}")
    logger.warning("⚠️ La aplicación iniciará pero sin base de datos")

# Importar rutas
from routes.whatsapp_routes import router as whatsapp_router
from routes.lead_routes import router as lead_router
from routes.producto_routes import router as producto_router

# Crear app
app = FastAPI(
    title="FRESST Chatbot API",
    description="API para chatbot WhatsApp de FRESST",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(whatsapp_router)
app.include_router(lead_router)
app.include_router(producto_router)

# ===== RUTAS BASE =====

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "app": "FRESST Chatbot API",
        "status": "online",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "FRESST Bot",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/info")
async def api_info():
    """Información de la API"""
    return {
        "app_name": os.getenv("APP_NAME", "FRESST Chatbot"),
        "bot_name": os.getenv("BOT_NAME", "Kliofer"),
        "company_name": os.getenv("COMPANY_NAME", "FRESST"),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

# ===== EVENTOS =====

@app.on_event("startup")
async def startup_event():
    logger.info("✅ Aplicación iniciada")
    logger.info(f"🤖 Bot: {os.getenv('BOT_NAME', 'Kliofer')}")
    logger.info(f"🏢 Empresa: {os.getenv('COMPANY_NAME', 'FRESST')}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("❌ Aplicación detenida")
    close_mongodb()

# ===== MAIN =====

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🚀 Iniciando servidor en {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development"
    )