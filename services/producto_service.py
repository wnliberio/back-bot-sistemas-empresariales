# ============================================================================
# RUTA: backend/services/producto_service.py
# DESCRIPCIÓN: Servicio de Productos - Gestión del catálogo
# USO: Buscar y obtener productos
# ============================================================================

import logging
from bson.objectid import ObjectId
from config.database import get_collection

logger = logging.getLogger(__name__)

def obtener_todos_productos() -> dict:
    """Obtiene todos los productos"""
    try:
        productos = get_collection("productos")
        resultado = list(productos.find())
        
        for p in resultado:
            p["_id"] = str(p["_id"])
        
        return {"success": True, "total": len(resultado), "data": resultado}
    except Exception as e:
        logger.error(f"❌ Error obteniendo productos: {e}")
        return {"success": False, "error": str(e)}

def obtener_productos_por_categoria(categoria: str) -> dict:
    """Obtiene productos de una categoría específica"""
    try:
        productos = get_collection("productos")
        resultado = list(productos.find({"categoria": categoria, "activo": True}))
        
        for p in resultado:
            p["_id"] = str(p["_id"])
        
        return {
            "success": True,
            "categoria": categoria,
            "total": len(resultado),
            "data": resultado
        }
    except Exception as e:
        logger.error(f"❌ Error obteniendo productos por categoría: {e}")
        return {"success": False, "error": str(e)}

def obtener_producto_por_id(id_producto: str) -> dict:
    """Obtiene un producto específico"""
    try:
        productos = get_collection("productos")
        producto = productos.find_one({"_id": ObjectId(id_producto)})
        
        if producto:
            producto["_id"] = str(producto["_id"])
            return {"success": True, "data": producto}
        
        return {"success": False, "mensaje": "Producto no encontrado"}
    except Exception as e:
        logger.error(f"❌ Error obteniendo producto: {e}")
        return {"success": False, "error": str(e)}

def obtener_categorias() -> dict:
    """Obtiene todas las categorías únicas"""
    try:
        productos = get_collection("productos")
        categorias = productos.distinct("categoria")
        
        return {"success": True, "data": categorias}
    except Exception as e:
        logger.error(f"❌ Error obteniendo categorías: {e}")
        return {"success": False, "error": str(e)}

def obtener_producto_por_nombre(nombre: str) -> dict:
    """Busca un producto por nombre"""
    try:
        productos = get_collection("productos")
        producto = productos.find_one({
            "nombre": {"$regex": nombre, "$options": "i"}
        })
        
        if producto:
            producto["_id"] = str(producto["_id"])
            return {"success": True, "data": producto}
        
        return {"success": False, "mensaje": "Producto no encontrado"}
    except Exception as e:
        logger.error(f"❌ Error buscando producto: {e}")
        return {"success": False, "error": str(e)}