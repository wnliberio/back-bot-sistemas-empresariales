# ============================================================================
# RUTA: backend/services/payment_service.py
# DESCRIPCIÓN: Servicio de Pagos v2 - Solo 2 opciones (contraentrega + presencial)
# USO: Gestionar pagos de forma simple y clara
# ============================================================================

import logging
from datetime import datetime
from config.database import get_collection

logger = logging.getLogger(__name__)

INFO_LOCAL = {
    "horario": "Martes a Domingo de 9:00 AM a 6:00 PM",
    "direccion": "Av. Maldonado e Islas Malvinas, junto a entrada de Ecovía Nueva Aurora",
    "ciudad": "Quito"
}

DIAS_ENTREGA = 2  # 2 días hábiles laborales

def detectar_opcion_pago(mensaje: str) -> dict:
    """
    Detecta SOLO 2 opciones de pago del cliente
    
    Args:
        mensaje: Mensaje del cliente
    
    Returns:
        dict con opción detectada
    """
    mensaje_lower = mensaje.lower()
    
    resultado = {
        "opcion_detectada": None,
        "es_contraentrega": False,
        "es_presencial": False,
        "confianza": False
    }
    
    # ⭐ CONTRAENTREGA: pago al recibir
    palabras_contraentrega = [
        "contraentrega", "contra entrega", "entregar", "a domicilio", 
        "enviar a casa", "lo entregas", "me lo envíes", "me lo mandes"
    ]
    
    if any(p in mensaje_lower for p in palabras_contraentrega):
        resultado["opcion_detectada"] = "contraentrega"
        resultado["es_contraentrega"] = True
        resultado["confianza"] = True
        logger.info(f"💳 Opción detectada: CONTRAENTREGA")
        return resultado
    
    # ⭐ PRESENCIAL: va al local
    palabras_presencial = [
        "presencial", "local", "voy al local", "me acerco", "voy a ir", 
        "paso por", "voy para allá", "en el local", "en tu local", "efectivo"
    ]
    
    if any(p in mensaje_lower for p in palabras_presencial):
        resultado["opcion_detectada"] = "presencial"
        resultado["es_presencial"] = True
        resultado["confianza"] = True
        logger.info(f"🏪 Opción detectada: PRESENCIAL")
        return resultado
    
    return resultado

def construir_respuesta_pago_contraentrega(total: float, nombre: str) -> str:
    """
    Construye respuesta para CONTRAENTREGA (pago al recibir)
    
    Args:
        total: Monto total de la compra
        nombre: Nombre del cliente
    
    Returns:
        Respuesta formateada
    """
    
    respuesta = f"""Perfecto {nombre}! ✅

📦 ENTREGA A DOMICILIO - PAGO AL RECIBIR:

Monto: ${total}
Entrega: {DIAS_ENTREGA} días hábiles laborales
Pago: Cuando recibas el producto

Te llamaremos para coordinar la hora de entrega.
¿Cuál es tu dirección de entrega?"""
    
    return respuesta

def construir_respuesta_pago_presencial(nombre: str) -> str:
    """
    Construye respuesta para COMPRA EN LOCAL (presencial)
    
    Args:
        nombre: Nombre del cliente
    
    Returns:
        Respuesta formateada
    """
    
    respuesta = f"""Excelente {nombre}! 🏪

🏪 COMPRA EN LOCAL:

📍 {INFO_LOCAL['direccion']}
⏰ {INFO_LOCAL['horario']}
🏙️  {INFO_LOCAL['ciudad']}

Puedes pasar cuando gustes.
¿Necesitas tu código de pedido para ir?"""
    
    return respuesta

def construir_respuesta_opciones_pago(total: float, nombre: str) -> str:
    """
    Construye respuesta con las 2 ÚNICAS opciones
    
    Args:
        total: Monto total
        nombre: Nombre del cliente
    
    Returns:
        Respuesta con opciones claras
    """
    
    respuesta = f"""Perfecto {nombre}! 1x Frigorífico ${total}

¿Cómo deseas:
1️⃣  Contraentrega (entrega a domicilio, pagas al recibir)
2️⃣  Presencial (compra en local)"""
    
    return respuesta

def generar_codigo_entrega(id_lead: str) -> str:
    """
    Genera código ÚNICO de entrega para el cliente
    
    Args:
        id_lead: ID del cliente
    
    Returns:
        Código con formato FRES-YYYY-XXXXXX
    """
    try:
        from datetime import datetime
        from bson import ObjectId
        
        # Obtener número de orden (secuencial)
        ordenes = get_collection("ordenes")
        total_ordenes = ordenes.count_documents({})
        numero_orden = total_ordenes + 1
        
        year = datetime.now().year
        codigo = f"FRES-{year}-{numero_orden:06d}"
        
        logger.info(f"✅ Código generado: {codigo}")
        return codigo
    
    except Exception as e:
        logger.error(f"❌ Error generando código: {e}")
        return f"FRES-ERROR"

def guardar_estado_pago_contraentrega(id_lead: str, total: float, direccion_entrega: str) -> dict:
    """
    Guarda estado de pago para CONTRAENTREGA
    
    Args:
        id_lead: ID del cliente
        total: Monto total
        direccion_entrega: Dirección a entregar
    
    Returns:
        Resultado
    """
    try:
        from bson import ObjectId
        
        leads = get_collection("leads")
        codigo = generar_codigo_entrega(id_lead)
        
        pago_info = {
            "tipo_pago": "contraentrega",
            "total": total,
            "estado": "pendiente_entrega",
            "codigo_entrega": codigo,
            "direccion_entrega": direccion_entrega,
            "pagado": False,
            "timestamp_pedido": datetime.now()
        }
        
        leads.update_one(
            {"_id": ObjectId(id_lead)},
            {"$set": {"pago_info": pago_info}}
        )
        
        logger.info(f"✅ Pago contraentrega guardado: {id_lead}")
        return {
            "success": True,
            "tipo": "contraentrega",
            "codigo": codigo,
            "data": pago_info
        }
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}

def guardar_estado_pago_presencial(id_lead: str, total: float) -> dict:
    """
    Guarda estado de pago para PRESENCIAL (local)
    
    Args:
        id_lead: ID del cliente
        total: Monto total
    
    Returns:
        Resultado
    """
    try:
        from bson import ObjectId
        
        leads = get_collection("leads")
        codigo = generar_codigo_entrega(id_lead)
        
        pago_info = {
            "tipo_pago": "presencial",
            "total": total,
            "estado": "pendiente_pago_local",
            "codigo_entrega": codigo,
            "pagado": False,
            "timestamp_pedido": datetime.now()
        }
        
        leads.update_one(
            {"_id": ObjectId(id_lead)},
            {"$set": {"pago_info": pago_info}}
        )
        
        logger.info(f"✅ Pago presencial guardado: {id_lead}")
        return {
            "success": True,
            "tipo": "presencial",
            "codigo": codigo,
            "data": pago_info
        }
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}

def confirmar_pago(id_lead: str) -> dict:
    """
    Marca pago como confirmado
    """
    try:
        from bson import ObjectId
        
        leads = get_collection("leads")
        
        leads.update_one(
            {"_id": ObjectId(id_lead)},
            {
                "$set": {
                    "pago_info.pagado": True,
                    "pago_info.timestamp_pago": datetime.now()
                }
            }
        )
        
        logger.info(f"✅ Pago confirmado: {id_lead}")
        return {"success": True}
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}