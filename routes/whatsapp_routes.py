# ============================================================================
# RUTA: backend/routes/whatsapp_routes.py
# DESCRIPCIÓN: Rutas para WhatsApp - CON DEBUG
# ============================================================================

from fastapi import APIRouter, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
import logging
import json
from datetime import datetime
from urllib.parse import quote

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

# ============================================================================
# ⭐ ENDPOINT: INICIAR CHAT DESDE FRONTEND
# ============================================================================

@router.post("/iniciar-chat")
async def iniciar_chat(request: Request):
    """Endpoint para iniciar chat desde el frontend"""
    
    logger.info("=" * 70)
    logger.info("🔴 ENDPOINT /iniciar-chat RECIBIÓ SOLICITUD POST")
    logger.info("=" * 70)
    
    try:
        # Leer JSON
        body = await request.json()
        logger.info(f"📨 Body recibido: {json.dumps(body, indent=2)}")
        
        nombre = body.get("nombre", "Cliente")
        email = body.get("email", "")
        referencia = body.get("referencia", "web")
        
        logger.info(f"✅ Nombre: {nombre}")
        logger.info(f"✅ Email: {email}")
        logger.info(f"✅ Referencia: {referencia}")
        
        # Número de Twilio
        NUMERO_FRESST = "14155238886"
        logger.info(f"✅ Número Twilio: {NUMERO_FRESST}")
        
        # Construir mensaje
        if "Interesado en" in nombre:
            producto = nombre.replace("Interesado en ", "").strip()
            mensaje_inicial = f"Hola! Me interesa conocer más sobre {producto} de FRESST"
            logger.info(f"✅ Producto detectado: {producto}")
        else:
            mensaje_inicial = "Hola! Me interesa conocer más sobre FRESST"
            logger.info(f"✅ Sin producto, usando genérico")
        
        logger.info(f"📨 Mensaje: {mensaje_inicial}")
        
        # Generar link
        mensaje_encoded = quote(mensaje_inicial)
        link_whatsapp = f"https://wa.me/{NUMERO_FRESST}?text={mensaje_encoded}"
        
        logger.info(f"✅ Link generado: {link_whatsapp[:50]}...")
        
        # Respuesta
        respuesta = {
            "success": True,
            "link": link_whatsapp,
            "mensaje": "Chat iniciado correctamente",
            "mensaje_inicial": mensaje_inicial
        }
        
        logger.info(f"✅ Respuesta OK: {json.dumps(respuesta, indent=2)}")
        logger.info("=" * 70)
        
        return respuesta
    
    except json.JSONDecodeError as e:
        logger.error(f"❌ ERROR JSON: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"JSON inválido: {str(e)}",
            "mensaje": "Error al parsear JSON"
        }
    
    except Exception as e:
        logger.error(f"❌ ERROR GENERAL: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "mensaje": f"Error: {str(e)}"
        }


# ============================================================================
# WEBHOOK: Recibir mensajes de Twilio
# ============================================================================

@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """Webhook de Twilio - Procesa mensajes entrantes"""
    try:
        form_data = await request.form()
        from_number = form_data.get("From", "").replace("whatsapp:", "")
        mensaje_usuario = form_data.get("Body", "")
        
        logger.info(f"📨 Mensaje WhatsApp de {from_number}: {mensaje_usuario}")
        
        resp = MessagingResponse()
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
    """Health check"""
    logger.info("✅ Health check")
    return {
        "status": "ok",
        "service": "WhatsApp API",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/test")
async def test_endpoint():
    """Test simple"""
    logger.info("✅ Test endpoint")
    return {
        "status": "ok",
        "mensaje": "El endpoint de test funciona"
    }