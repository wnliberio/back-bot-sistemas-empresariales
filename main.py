# ============================================================================
# RUTA: backend/main.py
# DESCRIPCIÓN: Aplicación FastAPI Principal - Con Frontend Integrado
# USO: python main.py (ejecutar el servidor)
# ============================================================================

import os
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import quote

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

# ⭐ SERVIR ARCHIVOS ESTÁTICOS (HTML + imágenes)
# ESTO DEBE IR ANTES DE INCLUIR LOS ROUTERS
if os.path.exists("static"):
    logger.info("✅ Sirviendo archivos estáticos desde carpeta /static")
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
else:
    logger.warning("⚠️ Carpeta /static no encontrada - Las imágenes no se cargarán")

# ⭐ ENDPOINT DIRECTO - Iniciar Chat
@app.post("/api/whatsapp/iniciar-chat")
async def iniciar_chat(request: Request):
    """Endpoint para iniciar chat desde el frontend"""
    try:
        data = await request.json()
        nombre = data.get("nombre", "Cliente")
        
        logger.info(f"📱 Chat iniciado: {nombre}")
        
        NUMERO_FRESST = "14155238886"
        
        if "Interesado en" in nombre:
            producto = nombre.replace("Interesado en ", "").strip()
            mensaje_inicial = f"Hola! Me interesa conocer más sobre {producto} de FRESST"
        else:
            mensaje_inicial = "Hola! Me interesa conocer más sobre FRESST"
        
        mensaje_encoded = quote(mensaje_inicial)
        link_whatsapp = f"https://wa.me/{NUMERO_FRESST}?text={mensaje_encoded}"
        
        logger.info(f"✅ Link WhatsApp generado")
        
        return {
            "success": True,
            "link": link_whatsapp,
            "mensaje_inicial": mensaje_inicial
        }
    
    except Exception as e:
        logger.error(f"❌ Error en iniciar-chat: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "mensaje": "Error al iniciar chat"
        }

# Incluir rutas (después del endpoint directo)
app.include_router(whatsapp_router)
app.include_router(lead_router)
app.include_router(producto_router)

# ===== RUTAS BASE =====

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
    logger.info("=" * 70)
    logger.info("✅ Aplicación iniciada")
    logger.info(f"🤖 Bot: {os.getenv('BOT_NAME', 'Kliofer')}")
    logger.info(f"🏢 Empresa: {os.getenv('COMPANY_NAME', 'FRESST')}")
    logger.info(f"🌍 Ambiente: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info("=" * 70)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("❌ Aplicación detenida")
    close_mongodb()

# ===== MAIN =====

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 10000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🚀 Iniciando servidor en {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development"
    )