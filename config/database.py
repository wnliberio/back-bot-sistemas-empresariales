# ============================================================================
# RUTA: backend/config/database.py
# DESCRIPCIÓN: Configuración de conexión a MongoDB Atlas
# USO: Importar en otros módulos para acceder a la BD
# ============================================================================

import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import logging

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI")

# Variables globales para acceso desde otros módulos
client = None
db = None
collections = {}

def connect_mongodb():
    """Conecta a MongoDB Atlas"""
    global client, db, collections
    
    try:
        if not MONGO_URI:
            raise ValueError("MONGO_URI no está configurado en .env")
        
        # Conectar con ServerApi como en el ejemplo de la plataforma
        client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsInsecure=True)
        
        # Verificar conexión
        client.admin.command('ping')
        logger.info("✅ Pinged your deployment. You successfully connected to MongoDB!")
        
        # Seleccionar base de datos
        db = client["fresst_chatbot"]
        
        # Inicializar referencias a colecciones
        collections = {
            'cuentas_bancarias': db["cuentas_bancarias"],
            'productos': db["productos"],
            'leads': db["leads"],
            'ordenes': db["ordenes"],
            'conversaciones_whatsapp': db["conversaciones_whatsapp"]
        }
        
        logger.info("✅ Conectado a base de datos: fresst_chatbot")
        return db
        
    except Exception as e:
        logger.error(f"❌ Error conectando a MongoDB: {e}")
        raise

def get_db():
    """Obtiene la instancia de base de datos"""
    if db is None:
        connect_mongodb()
    return db

def get_collection(collection_name):
    """Obtiene una colección específica"""
    global db
    if db is None:
        connect_mongodb()
    if collection_name not in collections:
        collections[collection_name] = db[collection_name]
    return collections[collection_name]

def close_mongodb():
    """Cierra la conexión a MongoDB"""
    global client
    if client:
        client.close()
        logger.info("✅ Conexión a MongoDB cerrada")