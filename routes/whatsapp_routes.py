# ============================================================================
# RUTA: backend/routes/whatsapp_routes.py - VERSION 2.0 (COMPLETA)
# DESCRIPCIÓN: Rutas WhatsApp - Webhook que PROCESA mensajes + chat inteligente
# ============================================================================

from fastapi import APIRouter, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
import logging
import json
from datetime import datetime
from urllib.parse import quote
from bson import ObjectId

# Importar servicios
from services.lead_service import (
    crear_lead,
    obtener_lead_por_telefono,
    guardar_mensaje,
    obtener_historial
)
from services.chat_service import procesar_mensaje
from services.whatsapp_service import send_whatsapp_message

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

# ============================================================================
# ⭐ ENDPOINT 1: INICIAR CHAT DESDE FRONTEND
# ============================================================================

@router.post("/iniciar-chat")
async def iniciar_chat(request: Request):
    """
    Endpoint para iniciar chat desde el frontend
    
    Flujo:
    1. Recibe nombre del cliente (opcional)
    2. Crea/busca lead en MongoDB
    3. Retorna link de WhatsApp + id_lead para tracking
    """
    
    logger.info("=" * 70)
    logger.info("📥 POST /api/whatsapp/iniciar-chat")
    logger.info("=" * 70)
    
    try:
        # Leer JSON
        body = await request.json()
        logger.info(f"📨 Body: {json.dumps(body, indent=2)}")
        
        nombre = body.get("nombre", "Cliente").strip()
        email = body.get("email", "").strip()
        referencia = body.get("referencia", "web")
        
        # Número de Twilio (Sandbox)
        NUMERO_FRESST = "14155238886"
        
        # 1️⃣ CREAR MENSAJE INICIAL
        if "Interesado en" in nombre:
            producto = nombre.replace("Interesado en ", "").strip()
            mensaje_inicial = f"Hola! Me interesa conocer más sobre {producto}"
        else:
            mensaje_inicial = "Hola! Me interesa conocer más sobre FRESST"
        
        logger.info(f"✅ Mensaje inicial: {mensaje_inicial}")
        
        # 2️⃣ GENERAR LINK WHATSAPP
        mensaje_encoded = quote(mensaje_inicial)
        link_whatsapp = f"https://wa.me/{NUMERO_FRESST}?text={mensaje_encoded}"
        
        logger.info(f"✅ Link generado: {link_whatsapp[:50]}...")
        
        # 3️⃣ RESPUESTA
        respuesta = {
            "success": True,
            "link": link_whatsapp,
            "mensaje": "Chat iniciado correctamente",
            "mensaje_inicial": mensaje_inicial,
            "referencia": referencia
        }
        
        logger.info(f"✅ Respuesta: {json.dumps(respuesta, indent=2)}")
        logger.info("=" * 70)
        
        return respuesta
    
    except json.JSONDecodeError as e:
        logger.error(f"❌ ERROR JSON: {e}", exc_info=True)
        return {"success": False, "error": f"JSON inválido: {str(e)}"}
    
    except Exception as e:
        logger.error(f"❌ ERROR GENERAL: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


# ============================================================================
# ⭐ ENDPOINT 2: WEBHOOK DE TWILIO - PROCESA MENSAJES ENTRANTES
# ============================================================================

@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """
    Webhook de Twilio - Procesa mensajes entrantes
    
    Flujo completo:
    1. Extrae número y mensaje de Twilio
    2. Busca/crea lead por número
    3. Extrae datos del mensaje (nombre, email, etc)
    4. Obtiene historial de conversación
    5. Procesa con Gemini (chat_service)
    6. Guarda respuesta en historial
    7. Envía respuesta por WhatsApp
    """
    
    logger.info("=" * 70)
    logger.info("📨 WEBHOOK DE TWILIO - Mensaje entrante")
    logger.info("=" * 70)
    
    try:
        # ============================================================
        # 1️⃣ EXTRAER DATOS DE TWILIO
        # ============================================================
        form_data = await request.form()
        from_number = form_data.get("From", "").replace("whatsapp:", "").strip()
        mensaje_usuario = form_data.get("Body", "").strip()
        message_sid = form_data.get("MessageSid", "").strip()
        
        logger.info(f"📱 De: {from_number}")
        logger.info(f"📝 Mensaje: {mensaje_usuario}")
        logger.info(f"📌 SID: {message_sid}")
        
        if not from_number or not mensaje_usuario:
            logger.error("❌ Falta número o mensaje")
            raise ValueError("Faltan datos del mensaje")
        
        # ============================================================
        # 2️⃣ BUSCAR/CREAR LEAD
        # ============================================================
        logger.info(f"🔍 Buscando lead por teléfono: {from_number}")
        
        # Buscar si ya existe
        resultado_busqueda = obtener_lead_por_telefono(from_number)
        
        if resultado_busqueda.get("success") and resultado_busqueda.get("data"):
            lead = resultado_busqueda["data"]
            id_lead = lead.get("_id")
            logger.info(f"✅ Lead encontrado: {id_lead}")
        else:
            # Crear nuevo lead
            logger.info(f"➕ Creando nuevo lead...")
            resultado_create = crear_lead(
                nombre=None,  # Se extrae del mensaje
                telefono=from_number,
                email=None
            )
            
            if resultado_create.get("success"):
                id_lead = resultado_create.get("id")
                logger.info(f"✅ Lead creado: {id_lead}")
            else:
                logger.error(f"❌ Error creando lead: {resultado_create}")
                raise ValueError("No se pudo crear lead")
        
        # ============================================================
        # 3️⃣ GUARDAR MENSAJE DEL CLIENTE EN HISTORIAL
        # ============================================================
        logger.info(f"💾 Guardando mensaje del cliente...")
        guardar_mensaje(
            id_lead=id_lead,
            numero_cliente=from_number,
            emisor="cliente",
            texto=mensaje_usuario,
            message_sid=message_sid
        )
        logger.info(f"✅ Mensaje guardado")
        
        # ============================================================
        # 4️⃣ OBTENER HISTORIAL COMPLETO
        # ============================================================
        logger.info(f"📜 Obteniendo historial...")
        resultado_historial = obtener_historial(id_lead, limite=10)
        
        if resultado_historial.get("success"):
            historial = resultado_historial.get("data", [])
            logger.info(f"✅ Historial con {len(historial)} mensajes")
        else:
            historial = []
            logger.warning(f"⚠️ No hay historial previo")
        
        # ============================================================
        # 5️⃣ PROCESAR CON GEMINI (chat_service)
        # ============================================================
        logger.info(f"🤖 Procesando con Gemini...")
        
        resultado_chat = procesar_mensaje(
            texto_usuario=mensaje_usuario,
            historial=historial,
            datos_lead={"_id": id_lead, "numero": from_number}
        )
        
        if resultado_chat.get("success"):
            respuesta_bot = resultado_chat.get("respuesta", "")
            logger.info(f"✅ Respuesta de Gemini: {respuesta_bot[:100]}...")
        else:
            logger.error(f"❌ Error en Gemini: {resultado_chat}")
            respuesta_bot = "Lo siento, hubo un error. Intenta de nuevo."
        
        # ============================================================
        # 6️⃣ GUARDAR RESPUESTA DEL BOT EN HISTORIAL
        # ============================================================
        logger.info(f"💾 Guardando respuesta del bot...")
        guardar_mensaje(
            id_lead=id_lead,
            numero_cliente=from_number,
            emisor="bot",
            texto=respuesta_bot,
            message_sid=None
        )
        logger.info(f"✅ Respuesta guardada")
        
        # ============================================================
        # 7️⃣ ENVIAR RESPUESTA POR WHATSAPP (usando Twilio)
        # ============================================================
        logger.info(f"📤 Enviando respuesta por WhatsApp...")
        
        # Crear respuesta XML de Twilio
        resp = MessagingResponse()
        resp.message(respuesta_bot)
        
        logger.info(f"✅ Respuesta enviada")
        logger.info("=" * 70)
        
        return Response(content=str(resp), media_type="application/xml")
    
    except Exception as e:
        logger.error(f"❌ ERROR EN WEBHOOK: {e}", exc_info=True)
        
        # Respuesta de error
        resp = MessagingResponse()
        resp.message("Error procesando tu mensaje. Intenta de nuevo.")
        
        return Response(content=str(resp), media_type="application/xml")


# ============================================================================
# 📊 ENDPOINT 3: GET CONVERSACIÓN (para debugging/admin)
# ============================================================================

@router.get("/conversacion/{id_lead}")
async def obtener_conversacion(id_lead: str):
    """Obtiene el historial completo de una conversación"""
    try:
        resultado = obtener_historial(id_lead, limite=50)
        return resultado
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# 🏥 HEALTH CHECK
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
        "mensaje": "WhatsApp API funcionando correctamente"
    }