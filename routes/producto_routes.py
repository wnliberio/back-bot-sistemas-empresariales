# ============================================================================
# RUTA: backend/routes/producto_routes.py
# DESCRIPCIÓN: Rutas/Endpoints para API de Productos
# USO: Obtener catálogo de productos vía API REST
# ENDPOINTS: /api/productos/*
# ============================================================================

from fastapi import APIRouter
from services.producto_service import (
    obtener_todos_productos,
    obtener_productos_por_categoria,
    obtener_producto_por_id,
    obtener_categorias,
    obtener_producto_por_nombre
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/productos", tags=["productos"])

@router.get("/")
async def listar_productos():
    """Obtiene todos los productos"""
    return obtener_todos_productos()

@router.get("/categorias")
async def listar_categorias():
    """Obtiene todas las categorías"""
    return obtener_categorias()

@router.get("/categoria/{categoria}")
async def productos_por_categoria(categoria: str):
    """Obtiene productos de una categoría específica"""
    return obtener_productos_por_categoria(categoria)

@router.get("/buscar")
async def buscar_producto(nombre: str):
    """Busca un producto por nombre"""
    return obtener_producto_por_nombre(nombre)

@router.get("/{id_producto}")
async def obtener_producto(id_producto: str):
    """Obtiene un producto específico"""
    return obtener_producto_por_id(id_producto)