# ============================================================================
# RUTA: backend/routes/whatsapp_routes_v4.py
# DESCRIPCIÓN: Webhook - Chat inteligente + Órdenes + NOMBRES CORRECTOS
# ============================================================================

from fastapi import APIRouter, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
import logging
import json
from datetime import datetime
from urllib.parse import quote
from services.lead_service_v2 import crear_lead, obtener_lead_por_telefono, actualizar_lead
from services.chat_service_v3 import procesar_mensaje
from services.sales_flow_v3 import detectar_metodo_pago, detectar_direccion, detectar_producto, obtener_precio_producto
from services.orden_service_v3 import crear_orden_contraentrega, crear_orden_presencial, guardar_metodo_pago_en_lead
from config.database import get_collection
from bson import ObjectId

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

# ============================================================================
# WEBHOOK: PROCESAR MENSAJES
# ============================================================================

@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """Webhook de Twilio - Chat inteligente + Órdenes"""
    try:
        logger.info("=" * 80)
        logger.info("[WEBHOOK] 📨 WEBHOOK RECIBIDO")
        logger.info("=" * 80)
        
        form_data = await request.form()
        from_number = form_data.get("From", "").replace("whatsapp:", "")
        mensaje_usuario = form_data.get("Body", "")
        
        logger.info(f"[WEBHOOK] 📱 Desde: {from_number}")
        logger.info(f"[WEBHOOK] 💬 Mensaje: {mensaje_usuario}")
        
        # ════════════════════════════════════════════════════════════════
        # PASO 1: BUSCAR LEAD POR TELÉFONO (normalizar formato)
        # ════════════════════════════════════════════════════════════════
        
        logger.info("[WEBHOOK] 🔍 Buscando lead por teléfono...")
        
        # Intentar con formato original (+593983200438)
        lead_existente = obtener_lead_por_telefono(from_number)
        
        # Si no encuentra, intentar sin el +
        if not lead_existente.get("success"):
            from_number_alt = from_number.lstrip("+")
            logger.info(f"[WEBHOOK] ℹ️  Intentando con formato alternativo: {from_number_alt}")
            lead_existente = obtener_lead_por_telefono(from_number_alt)
        
        # Si no encuentra, intentar con 0 al inicio (formato Ecuador)
        if not lead_existente.get("success"):
            from_number_alt = "0" + from_number[3:] if from_number.startswith("+593") else from_number
            logger.info(f"[WEBHOOK] ℹ️  Intentando con formato Ecuador: {from_number_alt}")
            lead_existente = obtener_lead_por_telefono(from_number_alt)
        
        if lead_existente.get("success") and lead_existente.get("data"):
            # LEAD ENCONTRADO - Usar datos guardados
            id_lead = str(lead_existente["data"]["_id"])
            nombre_cliente = lead_existente["data"].get("nombre", "Cliente")
            email_cliente = lead_existente["data"].get("email", "")
            
            # Si el nombre está vacío, usar "Cliente"
            if not nombre_cliente or nombre_cliente.strip() == "":
                nombre_cliente = "Cliente"
            
            logger.info(f"[WEBHOOK] ✅ Lead encontrado: {nombre_cliente}")
            logger.info(f"[WEBHOOK] 📧 Email: {email_cliente}")
        else:
            # INTENTA BÚSQUEDA ALTERNATIVA - Sin el +
            logger.info("[WEBHOOK] ⚠️  Intentando búsqueda alternativa...")
            
            # Remover + y intentar de nuevo
            telefono_sin_mas = from_number.lstrip("+")
            lead_existente_alt = obtener_lead_por_telefono(telefono_sin_mas)
            
            if lead_existente_alt.get("success") and lead_existente_alt.get("data"):
                id_lead = str(lead_existente_alt["data"]["_id"])
                nombre_cliente = lead_existente_alt["data"].get("nombre", "Cliente")
                email_cliente = lead_existente_alt["data"].get("email", "")
                
                if not nombre_cliente or nombre_cliente.strip() == "":
                    nombre_cliente = "Cliente"
                
                logger.info(f"[WEBHOOK] ✅ Lead encontrado (búsqueda alt): {nombre_cliente}")
                logger.info(f"[WEBHOOK] 📧 Email: {email_cliente}")
            else:
                # LEAD NUEVO - Crear
                logger.info("[WEBHOOK] 🆕 Lead nuevo, creando...")
                resultado_crear = crear_lead(
                    nombre="Cliente",
                    telefono=from_number,
                    email=None,
                    direccion=None
                )
                
                if resultado_crear.get("success"):
                    id_lead = resultado_crear["id"]
                    nombre_cliente = "Cliente"
                    email_cliente = ""
                    logger.info(f"[WEBHOOK] ✅ Lead creado: {id_lead}")
                else:
                    logger.error("[WEBHOOK] ❌ Error creando lead")
                    resp = MessagingResponse()
                    resp.message("Error en el servidor")
                    return Response(content=str(resp), media_type="application/xml")
        
        # ════════════════════════════════════════════════════════════════
        # PASO 2: PROCESAR MENSAJE CON CHAT INTELIGENTE
        # ════════════════════════════════════════════════════════════════
        
        logger.info(f"[WEBHOOK] 🤖 Procesando mensaje como: {nombre_cliente}...")
        resultado_chat = procesar_mensaje(id_lead, from_number, mensaje_usuario)
        
        if not resultado_chat.get("success"):
            logger.error(f"[WEBHOOK] ❌ Error chat: {resultado_chat.get('error')}")
            respuesta_kliofer = "Lo siento, hubo un error. Intenta de nuevo."
        else:
            respuesta_kliofer = resultado_chat.get("respuesta", "")
        
        logger.info(f"[WEBHOOK] ✅ Kliofer responde: {respuesta_kliofer[:60]}...")
        
        # ════════════════════════════════════════════════════════════════
        # PASO 3: GUARDAR CONVERSACIÓN
        # ════════════════════════════════════════════════════════════════
        
        logger.info("[WEBHOOK] 💾 Guardando en conversaciones...")
        try:
            conv_col = get_collection("conversaciones_whatsapp")
            
            # Guardar mensaje del cliente
            conv_col.update_one(
                {"id_lead": id_lead},
                {
                    "$push": {
                        "mensajes": {
                            "emisor": "cliente",
                            "texto": mensaje_usuario,
                            "timestamp": datetime.now()
                        }
                    },
                    "$set": {
                        "numero_cliente": from_number,
                        "nombre_cliente": nombre_cliente,
                        "timestamp": datetime.now()
                    }
                },
                upsert=True
            )
            
            # Guardar respuesta de Kliofer
            conv_col.update_one(
                {"id_lead": id_lead},
                {
                    "$push": {
                        "mensajes": {
                            "emisor": "bot",
                            "texto": respuesta_kliofer,
                            "timestamp": datetime.now()
                        }
                    }
                }
            )
            
            logger.info("[WEBHOOK] ✅ Conversación guardada")
        
        except Exception as e:
            logger.error(f"[WEBHOOK] ❌ Error guardando: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # PASO 4: DETECTAR INTENCIONES Y CREAR ÓRDENES
        # ════════════════════════════════════════════════════════════════
        
        logger.info("[WEBHOOK] 📊 Analizando intenciones...")
        
        producto = detectar_producto(mensaje_usuario)
        metodo_pago = detectar_metodo_pago(mensaje_usuario)
        direccion = detectar_direccion(mensaje_usuario)
        
        logger.info(f"[WEBHOOK] Intenciones:")
        logger.info(f"  - Producto: {producto}")
        logger.info(f"  - Método pago: {metodo_pago}")
        logger.info(f"  - Dirección: {direccion}")
        
        # ════════════════════════════════════════════════════════════════
        # PASO 4.1: CREAR ORDEN CONTRAENTREGA
        # ════════════════════════════════════════════════════════════════
        
        if producto and metodo_pago == "contraentrega" and direccion:
            logger.info("[WEBHOOK] 📦 Condiciones para CONTRAENTREGA...")
            
            precio = obtener_precio_producto(producto)
            
            if precio:
                resultado_orden = crear_orden_contraentrega(
                    id_lead=id_lead,
                    nombre_producto=producto,
                    cantidad=1,
                    precio_unitario=precio,
                    direccion=direccion
                )
                
                if resultado_orden.get("success"):
                    logger.info(f"[WEBHOOK] ✅ Orden creada: {resultado_orden['codigo']}")
                    guardar_metodo_pago_en_lead(id_lead, "contraentrega", precio, direccion)
                else:
                    logger.error(f"[WEBHOOK] ❌ Error orden: {resultado_orden.get('error')}")
        
        # ════════════════════════════════════════════════════════════════
        # PASO 4.2: CREAR ORDEN PRESENCIAL
        # ════════════════════════════════════════════════════════════════
        
        elif producto and metodo_pago == "presencial":
            logger.info("[WEBHOOK] 🏪 Condiciones para PRESENCIAL...")
            
            precio = obtener_precio_producto(producto)
            
            if precio:
                resultado_orden = crear_orden_presencial(
                    id_lead=id_lead,
                    nombre_producto=producto,
                    cantidad=1,
                    precio_unitario=precio
                )
                
                if resultado_orden.get("success"):
                    logger.info(f"[WEBHOOK] ✅ Orden creada: {resultado_orden['codigo']}")
                    guardar_metodo_pago_en_lead(id_lead, "presencial", precio)
                else:
                    logger.error(f"[WEBHOOK] ❌ Error orden: {resultado_orden.get('error')}")
        
        # ════════════════════════════════════════════════════════════════
        # PASO 5: ENVIAR RESPUESTA A WHATSAPP
        # ════════════════════════════════════════════════════════════════
        
        logger.info("[WEBHOOK] 📤 Enviando respuesta a WhatsApp...")
        
        resp = MessagingResponse()
        resp.message(respuesta_kliofer)
        
        logger.info("[WEBHOOK] ✅ WEBHOOK COMPLETADO")
        logger.info("=" * 80)
        
        return Response(content=str(resp), media_type="application/xml")
    
    except Exception as e:
        logger.error(f"[WEBHOOK] ❌ ERROR CRÍTICO: {e}", exc_info=True)
        resp = MessagingResponse()
        resp.message("Error en el servidor")
        return Response(content=str(resp), media_type="application/xml")


# ============================================================================
# ENDPOINT: CAPTURAR LEAD DESDE MODAL
# ============================================================================

@router.post("/capturar-lead")
async def capturar_lead(request: Request):
    """Endpoint para capturar datos del modal"""
    
    logger.info("=" * 80)
    logger.info("[MODAL] 📥 Capturando datos del modal")
    logger.info("=" * 80)
    
    try:
        body = await request.json()
        
        nombre = body.get("nombre", "").strip()
        telefono = body.get("telefono", "").strip()
        email = body.get("email", "").strip()
        producto = body.get("producto", "").strip()
        
        logger.info(f"[MODAL] 👤 Nombre: {nombre}")
        logger.info(f"[MODAL] 📱 Teléfono (original): {telefono}")
        logger.info(f"[MODAL] 📧 Email: {email}")
        logger.info(f"[MODAL] 📦 Producto: {producto}")
        
        if not nombre or not telefono:
            logger.error("[MODAL] ❌ Datos incompletos")
            return {"success": False, "error": "Nombre y teléfono requeridos"}
        
        # ════════════════════════════════════════════════════════════════
        # NORMALIZAR TELÉFONO: Convertir a +593...
        # ════════════════════════════════════════════════════════════════
        
        # Remover espacios y caracteres especiales
        telefono_limpio = telefono.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        # Si empieza con 0, convertir a +593
        if telefono_limpio.startswith("0"):
            telefono_normalizado = "+593" + telefono_limpio[1:]
        # Si empieza con 593, agregar +
        elif telefono_limpio.startswith("593"):
            telefono_normalizado = "+" + telefono_limpio
        # Si ya tiene +593, dejar como está
        elif telefono_limpio.startswith("+593"):
            telefono_normalizado = telefono_limpio
        else:
            telefono_normalizado = telefono_limpio
        
        logger.info(f"[MODAL] 📱 Teléfono (normalizado): {telefono_normalizado}")
        
        telefono = telefono_normalizado  # Usar el normalizado
        
        # ════════════════════════════════════════════════════════════════
        # BUSCAR O CREAR LEAD - CON NOMBRE GUARDADO
        # ════════════════════════════════════════════════════════════════
        
        logger.info(f"[MODAL] 🔍 Buscando lead por teléfono: {telefono}")
        
        # Intentar búsqueda EXACTA
        lead_existente = obtener_lead_por_telefono(telefono)
        
        # Si no encuentra, intentar sin el +
        if not lead_existente.get("success"):
            telefono_sin_plus = telefono.lstrip("+")
            logger.info(f"[MODAL] ℹ️  Intentando sin +: {telefono_sin_plus}")
            lead_existente = obtener_lead_por_telefono(telefono_sin_plus)
        
        # Si no encuentra, intentar con 0 al inicio (Ecuador)
        if not lead_existente.get("success"):
            if telefono.startswith("+593"):
                telefono_con_cero = "0" + telefono[4:]
            else:
                telefono_con_cero = "0" + telefono.lstrip("+")[2:]
            
            logger.info(f"[MODAL] ℹ️  Intentando con 0: {telefono_con_cero}")
            lead_existente = obtener_lead_por_telefono(telefono_con_cero)
        
        if lead_existente.get("success") and lead_existente.get("data"):
            # LEAD ENCONTRADO - ACTUALIZAR
            id_lead = str(lead_existente["data"]["_id"])
            
            datos = {"nombre": nombre}
            if email:
                datos["email"] = email
            
            actualizar_lead(id_lead, datos)
            logger.info(f"[MODAL] ✅ Lead ACTUALIZADO: {nombre} ({telefono})")
        else:
            # LEAD NO ENCONTRADO - CREAR NUEVO
            logger.info(f"[MODAL] 🆕 Lead no existe, creando nuevo...")
            
            resultado = crear_lead(
                nombre=nombre,
                telefono=telefono,
                email=email if email else None,
                direccion=None
            )
            
            if resultado.get("success"):
                id_lead = resultado["id"]
                logger.info(f"[MODAL] ✅ Lead CREADO: {nombre} ({telefono})")
            else:
                logger.error("[MODAL] ❌ Error creando lead")
                return {"success": False, "error": resultado.get("error")}
        
        # ════════════════════════════════════════════════════════════════
        # GENERAR LINK WHATSAPP
        # ════════════════════════════════════════════════════════════════
        
        numero_fresst = "+14155238886"
        
        if producto:
            mensaje = f"Hola! Me interesa conocer más sobre {producto} de FRESST"
        else:
            mensaje = "Hola! Me interesa conocer más sobre FRESST"
        
        mensaje_encoded = quote(mensaje)
        numero_limpio = numero_fresst.replace("+", "")
        link_whatsapp = f"https://wa.me/{numero_limpio}?text={mensaje_encoded}"
        
        logger.info(f"[MODAL] ✅ Link generado")
        logger.info("=" * 80)
        
        return {
            "success": True,
            "id_lead": id_lead,
            "link": link_whatsapp,
            "nombre": nombre,
            "telefono": telefono,
            "email": email,
            "producto": producto
        }
    
    except Exception as e:
        logger.error(f"[MODAL] ❌ Error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check"""
    logger.info("✅ Health check")
    return {
        "status": "ok",
        "service": "WhatsApp API v4",
        "timestamp": datetime.now().isoformat()
    }