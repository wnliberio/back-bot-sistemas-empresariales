# ============================================================================
# RUTA: backend/models/lead.py
# DESCRIPCIÓN: Modelo Pydantic para Leads (Clientes)
# TABLA: leads
# DOCUMENTOS: {"nombre": "Juan", "telefono": "+593983200438", ...}
# ============================================================================

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Lead(BaseModel):
    """Modelo para crear/actualizar lead"""
    nombre: Optional[str] = None
    telefono: str
    email: Optional[str] = None
    direccion_entrega: Optional[str] = None
    estado_compra: str = "lead"  # "lead" o "cliente"

class LeadResponse(BaseModel):
    """Modelo de respuesta"""
    id: str
    nombre: Optional[str]
    telefono: str
    email: Optional[str]
    direccion_entrega: Optional[str]
    estado_compra: str
    fecha_creacion: datetime
    timestamp: datetime

# Ejemplo de documento en MongoDB:
EJEMPLO = {
    "_id": "507f1f77bcf86cd799439011",
    "nombre": "Juan Pérez",
    "telefono": "+593983200438",
    "email": "juan@example.com",
    "direccion_entrega": "Calle 123, Número 45",
    "estado_compra": "cliente",
    "fecha_creacion": datetime.now(),
    "timestamp": datetime.now()
}