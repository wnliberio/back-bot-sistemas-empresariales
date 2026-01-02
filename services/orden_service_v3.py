# ============================================================================
# RUTA: backend/services/orden_service_v3.py
# DESCRIPCIÓN: Crear órdenes, generar códigos, guardar en BD
# ============================================================================

import logging
from datetime import datetime
from config.database import get_collection
from bson import ObjectId

logger = logging.getLogger(__name__)

# ============================================================================
# FUNCIÓN 1: GENERAR CÓDIGO ÚNICO DE ENTREGA
# ============================================================================

def generar_codigo_entrega():
    """Genera código único: FRES-2026-000001"""
    try:
        logger.info("[ORDEN_V3] 🔢 Generando código entrega...")
        
        ord_col = get_collection("ordenes")
        total = ord_col.count_documents({})
        numero = total + 1
        
        year = datetime.now().year
        codigo = f"FRES-{year}-{numero:06d}"
        
        logger.info(f"[ORDEN_V3] ✅ Código: {codigo}")
        return codigo
    
    except Exception as e:
        logger.error(f"[ORDEN_V3] ❌ Error: {e}")
        return "FRES-ERROR"

# ============================================================================
# FUNCIÓN 2: CREAR ORDEN CONTRAENTREGA
# ============================================================================

def crear_orden_contraentrega(id_lead, nombre_producto, cantidad, precio_unitario, direccion):
    """Crea orden para CONTRAENTREGA"""
    try:
        logger.info("=" * 80)
        logger.info("[ORDEN_V3] 📦 CREANDO ORDEN CONTRAENTREGA")
        logger.info(f"[ORDEN_V3] Lead: {id_lead}")
        logger.info(f"[ORDEN_V3] Producto: {nombre_producto} x{cantidad}")
        logger.info(f"[ORDEN_V3] Precio: ${precio_unitario} c/u")
        logger.info(f"[ORDEN_V3] Dirección: {direccion}")
        
        total = precio_unitario * cantidad
        codigo = generar_codigo_entrega()
        
        ord_col = get_collection("ordenes")
        
        orden_data = {
            "id_lead": ObjectId(id_lead),
            "numero_cliente": None,  # Se obtiene de lead después
            "productos": [
                {
                    "nombre": nombre_producto,
                    "precio": precio_unitario,
                    "cantidad": cantidad,
                    "subtotal": total
                }
            ],
            "total": total,
            "metodo_pago": "contraentrega",
            "direccion_entrega": direccion,
            "codigo_entrega": codigo,
            "estado": "pendiente_entrega",
            "pagado": False,
            "fecha_orden": datetime.now(),
            "timestamp": datetime.now()
        }
        
        result = ord_col.insert_one(orden_data)
        
        logger.info(f"[ORDEN_V3] ✅ Orden creada: {result.inserted_id}")
        logger.info(f"[ORDEN_V3] 💰 Total: ${total}")
        logger.info(f"[ORDEN_V3] 📍 Entrega: {direccion}")
        logger.info(f"[ORDEN_V3] 📋 Código: {codigo}")
        logger.info("=" * 80)
        
        return {
            "success": True,
            "id_orden": str(result.inserted_id),
            "codigo": codigo,
            "total": total,
            "metodo": "contraentrega",
            "direccion": direccion
        }
    
    except Exception as e:
        logger.error(f"[ORDEN_V3] ❌ Error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

# ============================================================================
# FUNCIÓN 3: CREAR ORDEN PRESENCIAL
# ============================================================================

def crear_orden_presencial(id_lead, nombre_producto, cantidad, precio_unitario):
    """Crea orden para PRESENCIAL"""
    try:
        logger.info("=" * 80)
        logger.info("[ORDEN_V3] 🏪 CREANDO ORDEN PRESENCIAL")
        logger.info(f"[ORDEN_V3] Lead: {id_lead}")
        logger.info(f"[ORDEN_V3] Producto: {nombre_producto} x{cantidad}")
        logger.info(f"[ORDEN_V3] Precio: ${precio_unitario} c/u")
        
        total = precio_unitario * cantidad
        codigo = generar_codigo_entrega()
        
        ord_col = get_collection("ordenes")
        
        orden_data = {
            "id_lead": ObjectId(id_lead),
            "numero_cliente": None,
            "productos": [
                {
                    "nombre": nombre_producto,
                    "precio": precio_unitario,
                    "cantidad": cantidad,
                    "subtotal": total
                }
            ],
            "total": total,
            "metodo_pago": "presencial",
            "direccion_entrega": None,  # No aplica
            "codigo_entrega": codigo,
            "estado": "pendiente_pago_local",
            "pagado": False,
            "fecha_orden": datetime.now(),
            "timestamp": datetime.now()
        }
        
        result = ord_col.insert_one(orden_data)
        
        logger.info(f"[ORDEN_V3] ✅ Orden creada: {result.inserted_id}")
        logger.info(f"[ORDEN_V3] 💰 Total: ${total}")
        logger.info(f"[ORDEN_V3] 📋 Código: {codigo}")
        logger.info(f"[ORDEN_V3] 📍 Local: Av. Maldonado e Islas Malvinas, Quito")
        logger.info("=" * 80)
        
        return {
            "success": True,
            "id_orden": str(result.inserted_id),
            "codigo": codigo,
            "total": total,
            "metodo": "presencial",
            "direccion_local": "Av. Maldonado e Islas Malvinas, Quito"
        }
    
    except Exception as e:
        logger.error(f"[ORDEN_V3] ❌ Error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

# ============================================================================
# FUNCIÓN 4: GUARDAR MÉTODO DE PAGO EN LEAD
# ============================================================================

def guardar_metodo_pago_en_lead(id_lead, metodo_pago, total, direccion=None):
    """Guarda método de pago en documento de lead"""
    try:
        logger.info(f"[ORDEN_V3] 💳 Guardando método pago en lead...")
        
        leads_col = get_collection("leads")
        
        pago_info = {
            "tipo_pago": metodo_pago,
            "total": total,
            "estado": "pendiente_entrega" if metodo_pago == "contraentrega" else "pendiente_pago",
            "pagado": False,
            "timestamp_pedido": datetime.now()
        }
        
        if direccion:
            pago_info["direccion_entrega"] = direccion
        
        leads_col.update_one(
            {"_id": ObjectId(id_lead)},
            {"$set": {"pago_info": pago_info}}
        )
        
        logger.info(f"[ORDEN_V3] ✅ Método pago guardado en lead")
        return {"success": True}
    
    except Exception as e:
        logger.error(f"[ORDEN_V3] ❌ Error: {e}")
        return {"success": False, "error": str(e)}

# ============================================================================
# FUNCIÓN 5: CONFIRMAR PAGO
# ============================================================================

def confirmar_pago(id_orden):
    """Marca orden como pagada"""
    try:
        logger.info(f"[ORDEN_V3] ✅ Confirmando pago de orden...")
        
        ord_col = get_collection("ordenes")
        
        ord_col.update_one(
            {"_id": ObjectId(id_orden)},
            {
                "$set": {
                    "pagado": True,
                    "estado": "pagado",
                    "timestamp_pago": datetime.now()
                }
            }
        )
        
        logger.info(f"[ORDEN_V3] ✅ Orden pagada: {id_orden}")
        return {"success": True}
    
    except Exception as e:
        logger.error(f"[ORDEN_V3] ❌ Error: {e}")
        return {"success": False, "error": str(e)}

# ============================================================================
# FUNCIÓN 6: OBTENER ORDEN POR ID
# ============================================================================

def obtener_orden(id_orden):
    """Obtiene orden de la BD"""
    try:
        logger.info(f"[ORDEN_V3] 📋 Buscando orden...")
        
        ord_col = get_collection("ordenes")
        orden = ord_col.find_one({"_id": ObjectId(id_orden)})
        
        if orden:
            orden["_id"] = str(orden["_id"])
            logger.info(f"[ORDEN_V3] ✅ Orden encontrada")
            return orden
        
        logger.warning(f"[ORDEN_V3] ⚠️  Orden no encontrada")
        return None
    
    except Exception as e:
        logger.error(f"[ORDEN_V3] ❌ Error: {e}")
        return None