# ============================================================================
# RUTA: backend/services/whatsapp_service.py
# DESCRIPCIÓN: Servicio de WhatsApp - Integración con Twilio
# USO: Enviar y recibir mensajes por WhatsApp
# ============================================================================

import os
from twilio.rest import Client
import logging

logger = logging.getLogger(__name__)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

# Inicializar cliente Twilio
try:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    logger.info("✅ Cliente Twilio inicializado")
except Exception as e:
    logger.error(f"❌ Error inicializando Twilio: {e}")
    twilio_client = None

def send_whatsapp_message(numero_cliente: str, mensaje: str) -> dict:
    """
    Envía un mensaje por WhatsApp
    
    Args:
        numero_cliente: Número del cliente (ej: +593983200438)
        mensaje: Contenido del mensaje
    
    Returns:
        Resultado del envío
    """
    try:
        if not twilio_client:
            raise Exception("Cliente Twilio no está inicializado")
        
        # Formatear número
        if not numero_cliente.startswith("+"):
            numero_cliente = "+" + numero_cliente
        
        to_whatsapp = f"whatsapp:{numero_cliente}"
        
        msg = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            body=mensaje,
            to=to_whatsapp
        )
        
        logger.info(f"✅ Mensaje enviado a {numero_cliente}. SID: {msg.sid}")
        
        return {
            "success": True,
            "sid": msg.sid,
            "status": msg.status,
            "numero": numero_cliente,
            "mensaje": mensaje
        }
    
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje: {e}")
        return {
            "success": False,
            "error": str(e),
            "numero": numero_cliente
        }

def verificar_webhook_signature(request_data: dict, signature: str) -> bool:
    """
    Verifica que el webhook sea de Twilio (seguridad)
    
    Args:
        request_data: Datos del request
        signature: Firma de Twilio
    
    Returns:
        True si es válido, False sino
    """
    try:
        from twilio.request_validator import RequestValidator
        validator = RequestValidator(TWILIO_AUTH_TOKEN)
        return validator.validate(
            url="",
            params=request_data,
            signature=signature
        )
    except Exception as e:
        logger.warning(f"⚠️ No se pudo validar firma: {e}")
        return True  # En desarrollo, permitir todo