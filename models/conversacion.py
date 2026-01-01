# ============================================================================
# RUTA: backend/models/conversacion.py
# DESCRIPCIÓN: Modelo Pydantic para Conversaciones WhatsApp
# TABLA: conversaciones_whatsapp
# DOCUMENTOS: {"id_lead": ObjectId, "mensajes": [...], ...}
# ============================================================================

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class Mensaje(BaseModel):
    """Un mensaje individual en la conversación"""
    emisor: str  # "cliente" o "bot"
    texto: str
    timestamp: datetime
    message_sid: Optional[str] = None  # ID de Twilio

class Conversacion(BaseModel):
    """Modelo para crear/actualizar conversación"""
    id_lead: str
    numero_cliente: str
    estado: str = "activa"  # activa, cerrada, etc

class ConversacionResponse(BaseModel):
    """Modelo de respuesta"""
    id: str
    id_lead: str
    numero_cliente: str
    mensajes: List[dict]
    estado: str
    fecha_inicio: datetime
    ultimo_mensaje: datetime

# Ejemplo de documento en MongoDB:
EJEMPLO = {
    "_id": "507f1f77bcf86cd799439011",
    "id_lead": "507f1f77bcf86cd799439012",
    "numero_cliente": "+593983200438",
    "estado": "activa",
    "mensajes": [
        {
            "emisor": "cliente",
            "texto": "Hola",
            "timestamp": datetime.now(),
            "message_sid": "SM..."
        },
        {
            "emisor": "bot",
            "texto": "¡Hola! Soy Kliofer de FRESST...",
            "timestamp": datetime.now(),
            "message_sid": "SM..."
        },
        {
            "emisor": "cliente",
            "texto": "Quiero frigoríficos",
            "timestamp": datetime.now(),
            "message_sid": "SM..."
        },
        {
            "emisor": "bot",
            "texto": "Tenemos frigoríficos a $2,500...",
            "timestamp": datetime.now(),
            "message_sid": "SM..."
        }
    ],
    "fecha_inicio": datetime.now(),
    "timestamp": datetime.now()
}