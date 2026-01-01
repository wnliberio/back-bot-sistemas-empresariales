# ============================================================================
# RUTA: backend/routes/whatsapp_routes.py (ACTUALIZAR SOLO EL ENDPOINT)
# DESCRIPCIÓN: Endpoint /iniciar-chat con mensaje personalizado del producto
# USO: El botón envía el nombre del producto y se incluye en el mensaje inicial
# ============================================================================

from fastapi import APIRouter, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
import logging
from datetime import datetime
from config.database import get_collection
from services.whatsapp_service import send_whatsapp_message
from services.chat_service import procesar_mensaje, generar_saludo
from services.lead_service import (
    crear_lead, 
    obtener_lead_por_telefono, 
    guardar_mensaje, 
    obtener_historial,
    actualizar_lead,
    actualizar_estado_compra,
    guardar_orden_de_compra
)
from services.sales_flow_service import extraer_datos_del_mensaje
from urllib.parse import quote

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

# ═══════════════════════════════════════════════════════════════════════════
# ⭐ ENDPOINT: INICIAR CHAT DESDE FRONTEND (CON MENSAJE PERSONALIZADO)
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/iniciar-chat")
async def iniciar_chat(request: Request):
    """
    Endpoint para iniciar chat desde el frontend
    
    📨 Recibe JSON:
    {
        "nombre": "Interesado en Asaderos",  ← IMPORTANTE: incluye el producto
        "email": "juan@example.com",
        "referencia": "producto_coccion"
    }
    
    ✅ Retorna:
    {
        "success": true,
        "link": "https://wa.me/14155238886?text=Hola!%20Me%20interesa%20conocer%20m%C3%A1s%20sobre%20el%20Asaderos%20de%20FRESST",
        "pre_lead_id": "...",
        "mensaje_inicial": "Hola! Me interesa conocer más sobre Asaderos de FRESST"
    }
    
    El usuario ve el mensaje en WhatsApp y puede enviarlo o modificarlo.
    """
    try:
        data = await request.json()
        
        nombre = data.get("nombre", "Cliente")
        email = data.get("email", "")
        referencia = data.get("referencia", "web")
        
        logger.info(f"📱 Solicitud iniciar chat desde: {referencia}")
        logger.info(f"   Nombre/Producto: {nombre}")
        
        # ════════════════════════════════════════════════════════════
        # CREAR PRE-LEAD
        # ════════════════════════════════════════════════════════════
        pre_leads = get_collection("pre_leads")
        
        pre_lead_data = {
            "nombre": nombre,
            "email": email,
            "referencia_origen": referencia,
            "estado": "visitante",
            "timestamp_visitante": datetime.now()
        }
        
        resultado = pre_leads.insert_one(pre_lead_data)
        pre_lead_id = str(resultado.inserted_id)
        
        logger.info(f"✅ Pre-lead creado: {pre_lead_id}")
        
        # ════════════════════════════════════════════════════════════
        # ⭐ CONSTRUIR MENSAJE PERSONALIZADO CON EL PRODUCTO
        # ════════════════════════════════════════════════════════════
        NUMERO_FRESST = "14155238886"
        
        # Si el nombre incluye "Interesado en" → es un producto específico
        if "Interesado en" in nombre:
            producto = nombre.replace("Interesado en ", "").strip()
            # Construir mensaje con el producto
            mensaje_inicial = f"Hola! Me interesa conocer más sobre {producto} de FRESST"
            logger.info(f"📦 Producto detectado: {producto}")
        else:
            # Mensaje genérico
            mensaje_inicial = "Hola! Me interesa conocer más sobre FRESST"
            logger.info(f"📦 Sin producto específico, usando mensaje genérico")
        
        logger.info(f"📨 Mensaje inicial a enviar: {mensaje_inicial}")
        
        # ════════════════════════════════════════════════════════════
        # CODIFICAR Y GENERAR LINK
        # ════════════════════════════════════════════════════════════
        mensaje_encoded = quote(mensaje_inicial)
        link_whatsapp = f"https://wa.me/{NUMERO_FRESST}?text={mensaje_encoded}"
        
        logger.info(f"✅ Link WhatsApp generado")
        logger.info(f"   Longitud: {len(link_whatsapp)} caracteres")
        
        return {
            "success": True,
            "link": link_whatsapp,
            "pre_lead_id": pre_lead_id,
            "mensaje": "Chat iniciado correctamente",
            "mensaje_inicial": mensaje_inicial  # Para debugging
        }
    
    except Exception as e:
        logger.error(f"❌ Error en iniciar-chat: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "mensaje": "Error al iniciar chat"
        }

# ═══════════════════════════════════════════════════════════════════════════
# RESTO DE ENDPOINTS (SIN CAMBIOS)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/obtener-pre-lead/{pre_lead_id}")
async def obtener_pre_lead(pre_lead_id: str):
    """Obtiene datos del pre-lead (para debugging)"""
    try:
        from bson import ObjectId
        
        pre_leads = get_collection("pre_leads")
        pre_lead = pre_leads.find_one({"_id": ObjectId(pre_lead_id)})
        
        if pre_lead:
            pre_lead["_id"] = str(pre_lead["_id"])
            return {"success": True, "data": pre_lead}
        else:
            return {"success": False, "error": "Pre-lead no encontrado"}
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}


def es_solo_saludo(mensaje: str) -> bool:
    """Detecta si es SOLO un saludo"""
    mensaje_lower = mensaje.lower().strip()
    
    saludos = [
        "hola", "buenos días", "buenas tardes", "buenas noches",
        "buenos", "buenas", "qué tal", "como estás", "cómo estás"
    ]
    
    for saludo in saludos:
        if mensaje_lower == saludo or mensaje_lower.startswith(saludo):
            if not any(p in mensaje_lower for p in ["frigorífico", "horno", "mesa", "precio", "quiero", "busco"]):
                return True
    
    return False

@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """Webhook de Twilio - Procesa mensajes entrantes"""
    try:
        form_data = await request.form()
        from_number = form_data.get("From", "").replace("whatsapp:", "")
        mensaje_usuario = form_data.get("Body", "")
        message_sid = form_data.get("MessageSid", "")
        
        logger.info(f"📨 Mensaje recibido de {from_number}: {mensaje_usuario}")
        
        resp = MessagingResponse()
        respuesta_bot = None
        lead_id = None
        
        try:
            datos_extraidos = extraer_datos_del_mensaje(mensaje_usuario)
            logger.info(f"📝 Datos extraídos: {datos_extraidos}")
            
            lead_result = obtener_lead_por_telefono(from_number)
            
            # CLIENTE NUEVO
            if not lead_result["success"]:
                logger.info(f"📝 CLIENTE NUEVO")
                
                lead_data = crear_lead(
                    telefono=from_number,
                    nombre=datos_extraidos.get("nombre")
                )
                
                if lead_data["success"]:
                    lead_id = lead_data["id"]
                    logger.info(f"✅ Lead creado: {lead_id}")
                    
                    chat_result = procesar_mensaje(
                        mensaje_usuario, 
                        historial=[], 
                        datos_lead={"nombre": datos_extraidos.get("nombre")}
                    )
                    if chat_result["success"]:
                        respuesta_bot = chat_result["respuesta"]
                    else:
                        respuesta_bot = "Lo siento, hubo un error. Intenta de nuevo."
                else:
                    respuesta_bot = "Error procesando tu solicitud"
            
            # CLIENTE EXISTENTE
            else:
                lead = lead_result["data"]
                lead_id = str(lead.get("_id", ""))
                nombre = lead.get("nombre") or "Cliente"
                logger.info(f"✅ Lead encontrado: {lead_id}")
                
                if datos_extraidos.get("nombre") and not lead.get("nombre"):
                    actualizar_lead(lead_id, {"nombre": datos_extraidos["nombre"]})
                
                if datos_extraidos.get("direccion") and not lead.get("direccion_entrega"):
                    actualizar_lead(lead_id, {"direccion_entrega": datos_extraidos["direccion"]})
                
                historial_result = obtener_historial(lead_id, limite=20)
                historial = historial_result.get("data", []) if historial_result["success"] else []
                logger.info(f"📚 Historial: {len(historial)} mensajes")
                
                chat_result = procesar_mensaje(mensaje_usuario, historial, nombre)
                if chat_result["success"]:
                    respuesta_bot = chat_result["respuesta"]
                else:
                    respuesta_bot = "Lo siento, no entendí. Intenta de nuevo."
        
        except Exception as inner_error:
            logger.error(f"❌ Error procesando: {inner_error}", exc_info=True)
            respuesta_bot = "Error procesando tu solicitud"
        
        # Agregar respuesta
        if respuesta_bot:
            resp.message(respuesta_bot)
            logger.info(f"✉️ Mensaje agregado a TwiML")
        
        # Guardar en MongoDB
        if lead_id:
            logger.info(f"💾 Guardando mensajes para lead: {lead_id}")
            
            guardar_mensaje(
                id_lead=lead_id,
                numero_cliente=from_number,
                emisor="cliente",
                texto=mensaje_usuario,
                message_sid=message_sid
            )
            
            if respuesta_bot:
                guardar_mensaje(
                    id_lead=lead_id,
                    numero_cliente=from_number,
                    emisor="bot",
                    texto=respuesta_bot,
                    message_sid=message_sid
                )
        
        logger.info(f"📤 Enviando respuesta TwiML")
        return Response(content=str(resp), media_type="application/xml")
    
    except Exception as e:
        logger.error(f"❌ Error en webhook: {e}", exc_info=True)
        resp = MessagingResponse()
        resp.message("Error en el servidor")
        return Response(content=str(resp), media_type="application/xml")

@router.get("/health")
async def health_check():
    """Health check"""
    return {"status": "ok", "service": "WhatsApp Webhook"}

@router.post("/send-message")
async def send_message(numero: str, mensaje: str):
    """Enviar mensaje manual"""
    try:
        result = send_whatsapp_message(numero, mensaje)
        return result
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}