# ============================================================================
# RUTA: backend/services/sales_flow_v3.py
# DESCRIPCIÓN: Detecta producto, cantidad, método pago, dirección, etapa
# ============================================================================

import logging
import re
from config.database import get_collection
from bson import ObjectId

logger = logging.getLogger(__name__)

# ============================================================================
# MAPEO DE PRODUCTOS
# ============================================================================

PRODUCTOS_MAP = {
    "frigorífico": "Frigoríficos",
    "frigorifico": "Frigoríficos",
    "frio": "Frigoríficos",
    "vitrina": "Vitrinas Horizontales",
    "horno": "Hornos",
    "freidora": "Freidoras",
    "cocina": "Cocinas",
    "asadero": "Asaderos",
    "salchipapera": "Salchipaperas",
    "mesa": "Mesas de Acero",
    "estantería": "Estanterías",
    "gondola": "Góndolas",
    "panera": "Paneras",
    "hotdog": "Carros de Hotdogs",
    "balanza": "Balanza",
    "bombonera": "Bomboneras"
}

# ============================================================================
# FUNCIÓN 1: DETECTAR PRODUCTO
# ============================================================================

def detectar_producto(mensaje):
    """Detecta si menciona un producto"""
    logger.info(f"[SALES_V3] 🔍 Detectando producto...")
    
    mensaje_lower = mensaje.lower()
    
    for palabra, producto in PRODUCTOS_MAP.items():
        if palabra in mensaje_lower:
            logger.info(f"[SALES_V3] ✅ Producto: {producto}")
            return producto
    
    logger.info("[SALES_V3] ❌ No detectado")
    return None

# ============================================================================
# FUNCIÓN 2: DETECTAR CANTIDAD
# ============================================================================

def detectar_cantidad(mensaje):
    """Detecta cantidad mencionada"""
    logger.info("[SALES_V3] 🔍 Detectando cantidad...")
    
    numeros = re.findall(r'\d+', mensaje)
    
    if numeros:
        cantidad = int(numeros[0])
        logger.info(f"[SALES_V3] ✅ Cantidad: {cantidad}")
        return cantidad
    
    logger.info("[SALES_V3] ℹ️  Default: 1")
    return 1

# ============================================================================
# FUNCIÓN 3: DETECTAR MÉTODO DE PAGO
# ============================================================================

def detectar_metodo_pago(mensaje):
    """Detecta contraentrega o presencial"""
    logger.info("[SALES_V3] 🔍 Detectando método pago...")
    
    msg_lower = mensaje.lower()
    
    # CONTRAENTREGA
    if any(p in msg_lower for p in [
        "contraentrega", "contra entrega", "entrega", "domicilio",
        "casa", "enviar", "delivery", "me lo entregas"
    ]):
        logger.info("[SALES_V3] ✅ Método: CONTRAENTREGA")
        return "contraentrega"
    
    # PRESENCIAL
    if any(p in msg_lower for p in [
        "presencial", "local", "voy", "paso", "efectivo",
        "en el local", "ir al local", "voy allá"
    ]):
        logger.info("[SALES_V3] ✅ Método: PRESENCIAL")
        return "presencial"
    
    logger.info("[SALES_V3] ❌ No detectado")
    return None

# ============================================================================
# FUNCIÓN 4: DETECTAR DIRECCIÓN
# ============================================================================

def detectar_direccion(mensaje):
    """Detecta si menciona dirección"""
    logger.info("[SALES_V3] 🔍 Detectando dirección...")
    
    msg_lower = mensaje.lower()
    
    # Si menciona palabras de dirección
    if any(p in msg_lower for p in [
        "avenida", "av.", "calle", "dirección", "número",
        "quito", "barrio", "zona", "sector"
    ]):
        logger.info(f"[SALES_V3] ✅ Dirección: {mensaje[:60]}...")
        return mensaje.strip()
    
    logger.info("[SALES_V3] ❌ No detectada")
    return None

# ============================================================================
# FUNCIÓN 5: OBTENER ETAPA DE VENTA
# ============================================================================

def obtener_etapa(id_lead):
    """
    Detecta en qué etapa del flujo está:
    - consulta: preguntando, sin intención clara
    - producto_seleccionado: eligió qué comprar
    - esperando_pago: debe elegir método
    - esperando_direccion: debe dar dirección (contraentrega)
    - venta_completada: pedido confirmado
    """
    try:
        logger.info("[SALES_V3] 📊 Detectando etapa...")
        
        conv_col = get_collection("conversaciones_whatsapp")
        resultado = conv_col.find_one({"id_lead": id_lead})
        
        if not resultado or "mensajes" not in resultado:
            logger.info("[SALES_V3] → Etapa: CONSULTA (sin historial)")
            return "consulta"
        
        mensajes = resultado["mensajes"]
        historial_texto = " ".join([m.get("texto", "").lower() for m in mensajes])
        
        # Lógica de etapas
        if "contraentrega" in historial_texto and "av." in historial_texto:
            logger.info("[SALES_V3] → Etapa: VENTA COMPLETADA")
            return "venta_completada"
        
        elif "contraentrega" in historial_texto or "presencial" in historial_texto:
            logger.info("[SALES_V3] → Etapa: ESPERANDO DIRECCIÓN")
            return "esperando_direccion"
        
        elif any(p in historial_texto for p in ["quiero", "compro", "dame", "necesito", "interesa"]):
            logger.info("[SALES_V3] → Etapa: ESPERANDO PAGO")
            return "esperando_pago"
        
        logger.info("[SALES_V3] → Etapa: CONSULTA")
        return "consulta"
    
    except Exception as e:
        logger.error(f"[SALES_V3] ❌ Error: {e}")
        return "consulta"

# ============================================================================
# FUNCIÓN 6: OBTENER PRECIO DE PRODUCTO
# ============================================================================

def obtener_precio_producto(nombre_producto):
    """Busca el precio del producto en BD"""
    try:
        logger.info(f"[SALES_V3] 💰 Buscando precio de {nombre_producto}...")
        
        prod_col = get_collection("productos")
        producto = prod_col.find_one({"nombre": nombre_producto})
        
        if producto:
            precio = producto.get("precio")
            logger.info(f"[SALES_V3] ✅ Precio: ${precio}")
            return precio
        
        logger.warning(f"[SALES_V3] ⚠️  Producto no encontrado")
        return None
    
    except Exception as e:
        logger.error(f"[SALES_V3] ❌ Error: {e}")
        return None

# ============================================================================
# FUNCIÓN 7: RESUMIR CONTEXTO DE VENTA
# ============================================================================

def resumir_venta(id_lead):
    """Resumen de la venta en progreso"""
    try:
        logger.info("[SALES_V3] 📋 Resumiendo contexto de venta...")
        
        conv_col = get_collection("conversaciones_whatsapp")
        resultado = conv_col.find_one({"id_lead": id_lead})
        
        resumen = {
            "producto": None,
            "cantidad": 1,
            "precio": None,
            "total": None,
            "metodo_pago": None,
            "direccion": None,
            "etapa": obtener_etapa(id_lead)
        }
        
        if resultado and "mensajes" in resultado:
            mensajes = resultado["mensajes"]
            historial_texto = " ".join([m.get("texto", "") for m in mensajes])
            
            # Detectar datos
            producto = detectar_producto(historial_texto)
            cantidad = detectar_cantidad(historial_texto)
            metodo = detectar_metodo_pago(historial_texto)
            direccion = detectar_direccion(historial_texto)
            
            if producto:
                resumen["producto"] = producto
                resumen["precio"] = obtener_precio_producto(producto)
                resumen["cantidad"] = cantidad
                
                if resumen["precio"]:
                    resumen["total"] = resumen["precio"] * cantidad
            
            if metodo:
                resumen["metodo_pago"] = metodo
            
            if direccion:
                resumen["direccion"] = direccion
        
        logger.info(f"[SALES_V3] ✅ Resumen: {resumen['etapa']}")
        return resumen
    
    except Exception as e:
        logger.error(f"[SALES_V3] ❌ Error: {e}")
        return None