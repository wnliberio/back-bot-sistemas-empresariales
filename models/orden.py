# ============================================================================
# RUTA: backend/models/orden.py
# DESCRIPCIÓN: Modelo Pydantic para Órdenes de Compra
# TABLA: ordenes
# DOCUMENTOS: {"id_lead": ObjectId, "productos": [...], "total": 2500, ...}
# ============================================================================

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ProductoEnOrden(BaseModel):
    """Producto dentro de una orden"""
    nombre: str
    precio: float
    cantidad: int
    subtotal: float

class ComprobantePago(BaseModel):
    """Comprobante de pago"""
    url_imagen: Optional[str] = None
    fecha_recibido: Optional[datetime] = None
    numero_transferencia: Optional[str] = None
    estado_verificacion: str = "pendiente"  # pendiente, verificado, rechazado

class Orden(BaseModel):
    """Modelo para crear/actualizar orden"""
    id_lead: str
    productos: List[ProductoEnOrden]
    total: float
    estado: str = "pendiente"  # pendiente, pagado, entregado
    notas: Optional[str] = None

class OrdenResponse(BaseModel):
    """Modelo de respuesta"""
    id: str
    id_lead: str
    productos: List[dict]
    total: float
    comprobante_pago: Optional[ComprobantePago]
    estado: str
    fecha_orden: datetime
    notas: Optional[str]

# Ejemplo de documento en MongoDB:
EJEMPLO = {
    "_id": "507f1f77bcf86cd799439011",
    "id_lead": "507f1f77bcf86cd799439012",
    "productos": [
        {
            "nombre": "Frigoríficos",
            "precio": 2500,
            "cantidad": 1,
            "subtotal": 2500
        }
    ],
    "total": 2500,
    "comprobante_pago": {
        "url_imagen": "https://cloudinary.com/...",
        "fecha_recibido": datetime.now(),
        "numero_transferencia": "123456789",
        "estado_verificacion": "verificado"
    },
    "estado": "pagado",
    "fecha_orden": datetime.now(),
    "notas": "Entrega urgente"
}