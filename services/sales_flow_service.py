# ============================================================================
# RUTA: backend/services/sales_flow_service.py
# DESCRIPCIÓN: Flujo de Ventas v5 - SIMPLE y CLARO (2 opciones)
# USO: Maneja flujo de venta de forma directa
# ============================================================================

import logging
import re
from datetime import datetime
from services.producto_service import obtener_todos_productos
from config.database import get_collection

logger = logging.getLogger(__name__)

INFO_LOCAL = {
    "horario": "Martes a Domingo de 9:00 AM a 6:00 PM",
    "direccion": "Av. Maldonado e Islas Malvinas, junto a entrada de Ecovía Nueva Aurora",
    "ciudad": "Quito"
}

DIAS_ENTREGA = 2

def extraer_datos_del_mensaje(mensaje: str) -> dict:
    """
    Extrae nombre, email, dirección del mensaje
    """
    datos = {
        "nombre": None,
        "apellido": None,
        "email": None,
        "direccion": None,
        "confirmacion_compra": False
    }
    
    mensaje_lower = mensaje.lower()
    
    # ⭐ EXTRAER NOMBRE
    patrones_nombre = [
        r'(?:me llamo|soy|con)\s+([A-Z][a-záéíóú]+)\s+([A-Z][a-záéíóú]+)',
        r'(?:me llamo|soy)\s+([A-Z][a-záéíóú]+)',
        r'(?:con)\s+([A-Z][a-záéíóú]+(?:\s+[A-Z][a-záéíóú]+)?)'
    ]
    
    for patron in patrones_nombre:
        match = re.search(patron, mensaje)
        if match:
            partes = match.group(1).split()
            datos["nombre"] = partes[0].capitalize()
            if len(partes) > 1:
                datos["apellido"] = partes[1].capitalize()
            elif match.lastindex >= 2:
                datos["apellido"] = match.group(2).capitalize()
            logger.info(f"📝 Nombre: {datos['nombre']} {datos['apellido'] or ''}")
            break
    
    # ⭐ EXTRAER EMAIL
    patron_email = r'[\w\.-]+@[\w\.-]+\.\w+'
    match_email = re.search(patron_email, mensaje)
    if match_email:
        datos["email"] = match_email.group(0)
        logger.info(f"📧 Email: {datos['email']}")
    
    # ⭐ EXTRAER DIRECCIÓN
    if any(p in mensaje_lower for p in ["dirección", "calle", "avenida", "av.", "av ", "jr."]):
        if "dirección:" in mensaje_lower:
            idx = mensaje_lower.index("dirección:") + len("dirección:")
            datos["direccion"] = mensaje[idx:].strip()
        else:
            for palabra in ["calle", "avenida", "av.", "av ", "jr."]:
                if palabra in mensaje_lower:
                    idx = mensaje_lower.index(palabra)
                    datos["direccion"] = mensaje[idx:].strip()
                    break
        
        if datos["direccion"]:
            logger.info(f"📍 Dirección: {datos['direccion']}")
    
    # ⭐ DETECTAR CONFIRMACIÓN
    palabras = ["si por favor", "si", "quiero", "compro", "dale", "adelante"]
    if any(p in mensaje_lower for p in palabras):
        datos["confirmacion_compra"] = True
        logger.info(f"✅ Confirmación detectada")
    
    return datos

def detectar_etapa_compra(historial: list) -> str:
    """
    Detecta en qué etapa está el cliente
    
    Retorna:
    - "consulta": preguntando, sin compra
    - "intención_clara": dijo que quiere
    - "esperando_metodo": necesita elegir cómo paga
    - "direccion_contraentrega": eligió contraentrega, pide dirección
    - "presencial_confirmado": va al local
    - "venta_completada": todo listo
    """
    
    hay_intension = False
    hay_confirmacion = False
    hay_contraentrega = False
    hay_presencial = False
    hay_direccion = False
    
    for msg in historial:
        texto = msg.get("texto", "").lower()
        
        # Detectar intención
        if any(p in texto for p in ["quiero", "compro", "dame", "necesito"]):
            hay_intension = True
        
        # Detectar confirmación
        if any(p in texto for p in ["si por favor", "si", "claro", "dale", "adelante"]):
            hay_confirmacion = True
        
        # Detectar contraentrega
        if any(p in texto for p in ["contraentrega", "entrega", "a domicilio", "a casa"]):
            hay_contraentrega = True
        
        # Detectar presencial
        if any(p in texto for p in ["presencial", "local", "voy", "paso", "efectivo"]):
            hay_presencial = True
        
        # Detectar dirección
        if any(p in texto for p in ["calle", "avenida", "av.", "dirección"]):
            hay_direccion = True
    
    # Lógica de estados
    if hay_presencial and hay_confirmacion:
        return "presencial_confirmado"
    elif hay_contraentrega and hay_direccion:
        return "venta_completada"
    elif hay_contraentrega and hay_confirmacion:
        return "direccion_contraentrega"
    elif hay_intension and not hay_confirmacion:
        return "esperando_metodo"
    elif hay_intension:
        return "intención_clara"
    else:
        return "consulta"

def construir_prompt_segun_etapa(
    etapa: str, 
    nombre: str,
    total: float,
    historial: list,
    mensaje_actual: str
) -> str:
    """
    Construye prompt ESPECÍFICO para cada etapa
    
    Args:
        etapa: etapa actual del flujo
        nombre: nombre del cliente
        total: monto de compra
        historial: últimos mensajes
        mensaje_actual: nuevo mensaje
    
    Returns:
        Prompt para Gemini
    """
    
    prompt_base = f"""🤖 KLIOFER - FRESST
Profesional, cálido, BREVE (máximo 2-3 líneas).
Nunca repitas información anterior.
Directo, sin rodeos.

INFORMACIÓN:
- Cliente: {nombre}
- Monto: ${total}
- Entrega: {DIAS_ENTREGA} días hábiles

ETAPA: {etapa}
"""
    
    if etapa == "consulta":
        prompt_base += """
INSTRUCCIONES:
- Responde la pregunta del cliente
- Breve, sin exagerar
- Máximo 2 líneas
"""
    
    elif etapa == "intención_clara":
        prompt_base += """
INSTRUCCIONES:
- Cliente dijo que quiere comprar
- Confirma: producto + cantidad + precio
- Ofrece las 2 ÚNICAS opciones:
  1️⃣  Contraentrega (entrega a domicilio, pagas al recibir)
  2️⃣  Presencial (compra en local)
- Máximo 3 líneas
"""
    
    elif etapa == "esperando_metodo":
        prompt_base += """
INSTRUCCIONES:
- Cliente eligió compra pero NO eligió método
- Pregunta CLARAMENTE:
  "¿Contraentrega o Presencial?"
- 1-2 líneas
- SIN confusión, SIN opciones extras
"""
    
    elif etapa == "direccion_contraentrega":
        prompt_base += """
INSTRUCCIONES:
- Cliente eligió CONTRAENTREGA
- Pregunta DIRECCIÓN:
  "¿Cuál es tu dirección de entrega?"
- Dile: "Entrega en {DIAS_ENTREGA} días hábiles"
- Dile: "Te llamaremos para coordinar"
- 2-3 líneas
"""
    
    elif etapa == "presencial_confirmado":
        prompt_base += """
INSTRUCCIONES:
- Cliente va al LOCAL
- Confirma donde está:
  📍 {INFO_LOCAL['direccion']}
  ⏰ {INFO_LOCAL['horario']}
- SIN pedir dirección
- Dile: "Tu código: [se genera]"
- Breve
"""
    
    elif etapa == "venta_completada":
        prompt_base += """
INSTRUCCIONES:
- VENTA LISTA
- Confirma RESUMEN:
  ✅ Producto + Precio
  ✅ Método (contraentrega/presencial)
  ✅ Dirección (si aplica)
  ✅ Tu código: [se genera]
- Agradece profesionalmente
- 3-4 líneas
"""
    
    # Agregar historial
    prompt_base += f"""

HISTORIAL (últimos 5 mensajes):
"""
    
    for msg in historial[-5:]:
        emisor = "Kliofer" if msg.get("emisor") == "bot" else nombre
        texto = msg.get("texto", "")[:50]
        prompt_base += f"{emisor}: {texto}\n"
    
    prompt_base += f"""
Cliente: {mensaje_actual}
Kliofer (breve, profesional):"""
    
    return prompt_base

def obtener_total_compra() -> float:
    """
    Obtiene total de compra (por ahora fijo, después se calcula)
    """
    return 2500  # Frigorífico default

def obtener_cuentas_bancarias() -> list:
    """NO USAMOS - Solo para referencia"""
    return []