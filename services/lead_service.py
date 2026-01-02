# ============================================================================
# RUTA: backend/services/lead_service.py
# DESCRIPCIÓN: Servicio de Leads - CRUD de clientes
# USO: Gestionar leads, órdenes y conversaciones
# ============================================================================

import logging
from bson.objectid import ObjectId
from datetime import datetime
from config.database import get_collection

logger = logging.getLogger(__name__)

# ===== LEADS =====

def crear_lead(nombre: str = None, telefono: str = None, email: str = None, direccion: str = None) -> dict:
    """Crea un nuevo lead"""
    try:
        if not telefono:
            return {"success": False, "error": "El teléfono es requerido"}
        
        # ════════════════════════════════════════════════════════════════
        # NORMALIZAR TELÉFONO AL GUARDAR
        # ════════════════════════════════════════════════════════════════
        
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
        
        logger.info(f"[LEAD] 📱 Teléfono normalizado: {telefono} → {telefono_normalizado}")
        
        leads = get_collection("leads")
        
        lead_data = {
            "nombre": nombre,
            "telefono": telefono_normalizado,  # ← GUARDAR NORMALIZADO
            "email": email,
            "direccion_entrega": direccion,
            "estado_compra": "lead",
            "fecha_creacion": datetime.now(),
            "timestamp": datetime.now()
        }
        
        result = leads.insert_one(lead_data)
        logger.info(f"✅ Lead creado: {result.inserted_id}")
        
        return {
            "success": True,
            "id": str(result.inserted_id),
            "data": lead_data
        }
    except Exception as e:
        logger.error(f"❌ Error creando lead: {e}")
        return {"success": False, "error": str(e)}

def obtener_lead_por_telefono(telefono: str) -> dict:
    """Obtiene un lead por teléfono - Busca en MÚLTIPLES FORMATOS"""
    try:
        logger.info(f"[LEAD] 🔍 Buscando: {telefono}")
        
        leads = get_collection("leads")
        
        # BÚSQUEDA 1: Exacta
        lead = leads.find_one({"telefono": telefono})
        if lead:
            lead["_id"] = str(lead["_id"])
            logger.info(f"[LEAD] ✅ Encontrado (exacta)")
            return {"success": True, "data": lead}
        
        # BÚSQUEDA 2: Convertir 0983200438 → +593983200438
        if telefono.startswith("0"):
            telefono_alt = "+593" + telefono[1:]
            logger.info(f"[LEAD] ℹ️  Intentando: {telefono_alt}")
            lead = leads.find_one({"telefono": telefono_alt})
            if lead:
                lead["_id"] = str(lead["_id"])
                logger.info(f"[LEAD] ✅ Encontrado (con +593)")
                return {"success": True, "data": lead}
        
        # BÚSQUEDA 3: Convertir +593983200438 → 0983200438
        if telefono.startswith("+593"):
            telefono_alt = "0" + telefono[4:]
            logger.info(f"[LEAD] ℹ️  Intentando: {telefono_alt}")
            lead = leads.find_one({"telefono": telefono_alt})
            if lead:
                lead["_id"] = str(lead["_id"])
                logger.info(f"[LEAD] ✅ Encontrado (con 0)")
                return {"success": True, "data": lead}
        
        # BÚSQUEDA 4: Sin el +
        telefono_sin_plus = telefono.lstrip("+")
        if telefono_sin_plus != telefono:
            logger.info(f"[LEAD] ℹ️  Intentando: {telefono_sin_plus}")
            lead = leads.find_one({"telefono": telefono_sin_plus})
            if lead:
                lead["_id"] = str(lead["_id"])
                logger.info(f"[LEAD] ✅ Encontrado (sin +)")
                return {"success": True, "data": lead}
        
        logger.warning(f"[LEAD] ❌ No encontrado")
        return {"success": False, "mensaje": "Lead no encontrado"}
    except Exception as e:
        logger.error(f"❌ Error obteniendo lead: {e}")
        return {"success": False, "error": str(e)}

def actualizar_lead(lead_id: str, datos: dict) -> dict:
    """Actualiza datos de un lead"""
    try:
        leads = get_collection("leads")
        
        datos_actualizar = {**datos, "timestamp": datetime.now()}
        
        result = leads.update_one(
            {"_id": ObjectId(lead_id)},
            {"$set": datos_actualizar}
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ Lead actualizado: {lead_id}")
            return {"success": True, "mensaje": "Lead actualizado"}
        
        return {"success": False, "mensaje": "Lead no encontrado"}
    except Exception as e:
        logger.error(f"❌ Error actualizando lead: {e}")
        return {"success": False, "error": str(e)}

def actualizar_estado_compra(lead_id: str, nuevo_estado: str) -> dict:
    """Actualiza el estado de compra de un lead"""
    try:
        leads = get_collection("leads")
        
        result = leads.update_one(
            {"_id": ObjectId(lead_id)},
            {"$set": {"estado_compra": nuevo_estado, "timestamp": datetime.now()}}
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ Estado de compra actualizado: {nuevo_estado}")
            return {"success": True}
        
        return {"success": False}
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}

def guardar_orden_de_compra(id_lead: str, productos: list, total: float, metodo_pago: str, direccion_entrega: str = None) -> dict:
    """Guarda una orden de compra"""
    try:
        ordenes = get_collection("ordenes")
        
        orden_data = {
            "id_lead": ObjectId(id_lead),
            "productos": productos,
            "total": total,
            "metodo_pago": metodo_pago,
            "direccion_entrega": direccion_entrega,
            "estado": "pendiente",
            "fecha_orden": datetime.now()
        }
        
        result = ordenes.insert_one(orden_data)
        logger.info(f"✅ Orden creada: {result.inserted_id}")
        
        return {
            "success": True,
            "id": str(result.inserted_id)
        }
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}

# ===== CONVERSACIONES =====

def guardar_mensaje(id_lead: str, numero_cliente: str, emisor: str, texto: str, message_sid: str = None) -> dict:
    """Guarda un mensaje en el historial"""
    try:
        conversaciones = get_collection("conversaciones_whatsapp")
        
        mensaje = {
            "emisor": emisor,
            "texto": texto,
            "timestamp": datetime.now(),
            "message_sid": message_sid
        }
        
        conversaciones.update_one(
            {"id_lead": id_lead},
            {
                "$push": {"mensajes": mensaje},
                "$set": {"numero_cliente": numero_cliente, "timestamp": datetime.now()}
            },
            upsert=True
        )
        
        logger.info(f"✅ Mensaje guardado para lead: {id_lead}")
        return {"success": True, "mensaje": "Mensaje guardado"}
    except Exception as e:
        logger.error(f"❌ Error guardando mensaje: {e}")
        return {"success": False, "error": str(e)}

def obtener_historial(id_lead: str, limite: int = 20) -> dict:
    """Obtiene el historial de una conversación"""
    try:
        conversaciones = get_collection("conversaciones_whatsapp")
        result = conversaciones.find_one({"id_lead": id_lead})
        
        if result and "mensajes" in result:
            mensajes = result["mensajes"][-limite:]
            return {"success": True, "data": mensajes}
        
        return {"success": True, "data": []}
    except Exception as e:
        logger.error(f"❌ Error obteniendo historial: {e}")
        return {"success": False, "error": str(e)}