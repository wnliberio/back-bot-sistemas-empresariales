from fastapi import APIRouter, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
import logging
from datetime import datetime
from urllib.parse import quote

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

@router.post("/iniciar-chat")
async def iniciar_chat(request: Request):
    try:
        data = await request.json()
        nombre = data.get("nombre", "Cliente")
        
        NUMERO_FRESST = "14155238886"
        
        if "Interesado en" in nombre:
            producto = nombre.replace("Interesado en ", "").strip()
            mensaje_inicial = f"Hola! Me interesa conocer más sobre {producto} de FRESST"
        else:
            mensaje_inicial = "Hola! Me interesa conocer más sobre FRESST"
        
        mensaje_encoded = quote(mensaje_inicial)
        link_whatsapp = f"https://wa.me/{NUMERO_FRESST}?text={mensaje_encoded}"
        
        logger.info(f"✅ Chat iniciado: {nombre}")
        
        return {
            "success": True,
            "link": link_whatsapp,
            "mensaje_inicial": mensaje_inicial
        }
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}

@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    try:
        form_data = await request.form()
        resp = MessagingResponse()
        resp.message("¡Hola! Un asesor te atenderá pronto.")
        return Response(content=str(resp), media_type="application/xml")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        resp = MessagingResponse()
        resp.message("Error")
        return Response(content=str(resp), media_type="application/xml")

@router.get("/health")
async def health_check():
    return {"status": "ok"}