# ============================================================================
# RUTA: backend/routes/lead_routes.py
# DESCRIPCIÓN: Rutas/Endpoints para API de Leads - SIMPLIFICADAS
# USO: Gestionar leads vía API REST
# ENDPOINTS: /api/leads/*
# ============================================================================

from fastapi import APIRouter
from services.lead_service import (
    crear_lead, 
    obtener_lead_por_telefono, 
    actualizar_lead
    # crear_orden, obtener_ordenes_por_lead, actualizar_estado_orden  # COMENTADAS
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/leads", tags=["leads"])

# ===== LEADS =====

@router.post("/crear")
async def crear_nuevo_lead(nombre: str = None, telefono: str = None, email: str = None, direccion: str = None):
    """Crea un nuevo lead"""
    return crear_lead(nombre, telefono, email, direccion)

@router.get("/{telefono}")
async def obtener_lead(telefono: str):
    """Obtiene un lead por teléfono"""
    return obtener_lead_por_telefono(telefono)

@router.put("/{lead_id}")
async def actualizar_datos_lead(lead_id: str, nombre: str = None, email: str = None, direccion: str = None):
    """Actualiza datos de un lead"""
    datos = {}
    if nombre:
        datos["nombre"] = nombre
    if email:
        datos["email"] = email
    if direccion:
        datos["direccion_entrega"] = direccion
    return actualizar_lead(lead_id, datos)

# ===== ÓRDENES - COMENTADAS TEMPORALMENTE =====
# Las órdenes se gestionan directamente desde whatsapp_routes.py

# @router.post("/{id_lead}/ordenes/crear")
# async def crear_nueva_orden(id_lead: str, productos: list, total: float, notas: str = None):
#     """Crea una nueva orden para un lead"""
#     return crear_orden(id_lead, productos, total, notas)
#
# @router.get("/{id_lead}/ordenes")
# async def obtener_ordenes(id_lead: str):
#     """Obtiene órdenes de un lead"""
#     return obtener_ordenes_por_lead(id_lead)
#
# @router.put("/ordenes/{id_orden}/estado")
# async def actualizar_orden(id_orden: str, nuevo_estado: str):
#     """Actualiza el estado de una orden"""
#     return actualizar_estado_orden(id_orden, nuevo_estado)

@router.get("/health")
async def health_check():
    """Health check"""
    return {"status": "ok", "service": "leads"}