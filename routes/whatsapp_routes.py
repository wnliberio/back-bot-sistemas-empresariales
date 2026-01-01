# ============================================================================
# RUTA: backend/routes/whatsapp_routes.py
# DESCRIPCIÓN: Rutas para WhatsApp - Iniciar chat y webhook
# ============================================================================

from fastapi import APIRouter, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
import logging
from datetime import datetime
from urllib.parse import quote

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

# ============================================================================
# ⭐ ENDPOINT: INICIAR CHAT DESDE FRONTEND
# ============================================================================

@router.post("/iniciar-chat")
async def iniciar_chat(request: Request):
    """
    Endpoint para iniciar chat desde el frontend
    
    Recibe JSON:
    {
        "nombre": "Interesado en Frigoríficos",
        "email": "cliente@example.com",
        "referencia": "producto_refrigeracion"
    }
    
    Retorna link de WhatsApp con mensaje personalizado
    """
    try:
        data = await request.json()
        
        nombre = data.get("nombre", "Cliente")
        email = data.get("email", "")
        referencia = data.get("referencia", "web")
        
        logger.info(f"📱 Solicitud iniciar chat desde: {referencia}")
        logger.info(f"   Nombre/Producto: {nombre}")
        
        # Número de Twilio
        NUMERO_FRESST = "14155238886"
        
        # Construir mensaje personalizado
        if "Interesado en" in nombre:
            producto = nombre.replace("Interesado en ", "").strip()
            mensaje_inicial = f"Hola! Me interesa conocer más sobre {producto} de FRESST"
        else:
            mensaje_inicial = "Hola! Me interesa conocer más sobre FRESST"
        
        logger.info(f"📨 Mensaje inicial: {mensaje_inicial}")
        
        # Generar link WhatsApp
        mensaje_encoded = quote(mensaje_inicial)
        link_whatsapp = f"https://wa.me/{NUMERO_FRESST}?text={mensaje_encoded}"
        
        logger.info(f"✅ Link WhatsApp generado")
        
        return {
            "success": True,
            "link": link_whatsapp,
            "mensaje": "Chat iniciado correctamente",
            "mensaje_inicial": mensaje_inicial
        }
    
    except Exception as e:
        logger.error(f"❌ Error en iniciar-chat: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "mensaje": "Error al iniciar chat"
        }


# ============================================================================
# WEBHOOK: Recibir mensajes de Twilio
# ============================================================================

@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """Webhook de Twilio - Procesa mensajes entrantes de WhatsApp"""
    try:
        form_data = await request.form()
        from_number = form_data.get("From", "").replace("whatsapp:", "")
        mensaje_usuario = form_data.get("Body", "")
        message_sid = form_data.get("MessageSid", "")
        
        logger.info(f"📨 Mensaje recibido de {from_number}: {mensaje_usuario}")
        
        resp = MessagingResponse()
        
        # Respuesta automática
        respuesta = "¡Hola! Gracias por contactarnos. Un asesor te atenderá pronto."
        resp.message(respuesta)
        
        logger.info(f"✅ Respuesta enviada")
        
        return Response(content=str(resp), media_type="application/xml")
    
    except Exception as e:
        logger.error(f"❌ Error en webhook: {e}", exc_info=True)
        resp = MessagingResponse()
        resp.message("Error en el servidor")
        return Response(content=str(resp), media_type="application/xml")


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check para WhatsApp routes"""
    return {
        "status": "ok",
        "service": "WhatsApp API",
        "timestamp": datetime.now().isoformat()
    }