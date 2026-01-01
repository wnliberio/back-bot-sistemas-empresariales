# ============================================================================
# RUTA: backend/models/producto.py
# DESCRIPCIÓN: Modelo Pydantic para Productos
# TABLA: productos
# DOCUMENTOS: {"nombre": "Frigoríficos", "categoria": "refrigeracion", ...}
# ============================================================================

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Producto(BaseModel):
    """Modelo para crear/actualizar producto"""
    nombre: str
    categoria: str  # refrigeracion, coccion, mobiliario, especiales
    precio: float
    caracteristicas: Optional[str] = None
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None
    activo: bool = True

class ProductoResponse(BaseModel):
    """Modelo de respuesta"""
    id: str
    nombre: str
    categoria: str
    precio: float
    caracteristicas: Optional[str]
    descripcion: Optional[str]
    imagen_url: Optional[str]
    activo: bool
    fecha_creacion: datetime

# Ejemplo de documento en MongoDB:
EJEMPLO = {
    "_id": "507f1f77bcf86cd799439011",
    "nombre": "Frigoríficos",
    "categoria": "refrigeracion",
    "precio": 2500,
    "caracteristicas": "Capacidad 800L, Consumo 150W, Garantía 2 años",
    "descripcion": "Frigoríficos profesionales para negocios gastronómicos",
    "imagen_url": None,
    "activo": True,
    "fecha_creacion": datetime.now()
}