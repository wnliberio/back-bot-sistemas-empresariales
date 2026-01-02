# ============================================================================
# RUTA: backend/services/chat_service_v3.py
# DESCRIPCIÓN: Chat inteligente - Lee BD, contexto completo, LOGS TODO
# ============================================================================

import logging
from datetime import datetime
from config.gemini_config import get_gemini_response
from config.database import get_collection
from bson import ObjectId

logger = logging.getLogger(__name__)

# ============================================================================
# INFORMACIÓN DE FRESST (Del sitio web)
# ============================================================================

INFO_FRESST = """
🏢 FRESST - Líderes en Equipamiento Profesional

📝 SOBRE FRESST:
Somos Fresst, líderes en equipamiento profesional para negocios gastronómicos y comerciales.
Con años de experiencia, nos especializamos en refrigeración, cocción, mobiliario y equipos especiales.

📍 UBICACIÓN: Av. Maldonado e Islas Malvinas, junto a Ecovía Nueva Aurora, Quito
⏰ HORARIO: Martes a Domingo, 9:00 AM - 6:00 PM
🚚 ENTREGA: 2-3 días hábiles en toda la ciudad
✅ GARANTÍA: 1.5-2 años en todos los productos

💬 ATENCIÓN: Respuesta inmediata por WhatsApp en tiempo real

🎯 ¿POR QUÉ ELEGIRNOS?
✓ Respuesta Inmediata: Atención personalizada 24/7
✓ Calidad Garantizada: Marcas profesionales de confianza
✓ Entrega Rápida: Instalación incluida
"""

# ============================================================================
# FUNCIÓN 1: OBTENER CATÁLOGO DE PRODUCTOS
# ============================================================================

def obtener_catalogo_productos():
    """Lee TODOS los productos de MongoDB"""
    try:
        logger.info("[CHAT_V3] 📦 Obteniendo catálogo...")
        
        productos_col = get_collection("productos")
        productos = list(productos_col.find({"activo": True}))
        
        logger.info(f"[CHAT_V3] ✅ {len(productos)} productos en BD")
        
        catalogo = {}
        for prod in productos:
            cat = prod.get("categoria", "otros")
            if cat not in catalogo:
                catalogo[cat] = []
            
            catalogo[cat].append({
                "nombre": prod.get("nombre"),
                "precio": prod.get("precio"),
                "caracteristicas": prod.get("caracteristicas", "")
            })
        
        # Texto para Gemini
        texto = "\n📦 CATÁLOGO COMPLETO DE PRODUCTOS:\n"
        categorias_map = {
            "refrigeracion": "🧊 REFRIGERACIÓN",
            "coccion": "🔥 COCCIÓN",
            "mobiliario": "🪑 MOBILIARIO",
            "especiales": "⚙️ EQUIPOS ESPECIALES"
        }
        
        for cat, label in categorias_map.items():
            if cat in catalogo:
                texto += f"\n{label}:\n"
                for prod in catalogo[cat]:
                    texto += f"  • {prod['nombre']}: ${prod['precio']}"
                    if prod['caracteristicas']:
                        texto += f" - {prod['caracteristicas']}"
                    texto += "\n"
        
        logger.info(f"[CHAT_V3] ✅ Catálogo formateado ({len(texto)} caracteres)")
        return texto
    
    except Exception as e:
        logger.error(f"[CHAT_V3] ❌ Error catálogo: {e}")
        return "\n📦 CATÁLOGO: [Error obteniendo catálogo]"

# ============================================================================
# FUNCIÓN 2: OBTENER HISTORIAL DEL CHAT
# ============================================================================

def obtener_historial(id_lead, limite=10):
    """Obtiene últimos N mensajes"""
    try:
        logger.info(f"[CHAT_V3] 📜 Historial de {id_lead} (últimos {limite})...")
        
        conv_col = get_collection("conversaciones_whatsapp")
        resultado = conv_col.find_one({"id_lead": id_lead})
        
        if not resultado or "mensajes" not in resultado:
            logger.info("[CHAT_V3] ℹ️  Sin historial previo")
            return ""
        
        mensajes = resultado["mensajes"][-limite:]
        logger.info(f"[CHAT_V3] ✅ {len(mensajes)} mensajes en historial")
        
        texto = "\n💬 HISTORIAL DEL CHAT:\n"
        for msg in mensajes:
            emisor = "👤 Cliente" if msg.get("emisor") == "cliente" else "🤖 Kliofer"
            texto_msg = msg.get("texto", "")[:100]  # Limitar a 100 caracteres
            texto += f"{emisor}: {texto_msg}\n"
        
        return texto
    
    except Exception as e:
        logger.error(f"[CHAT_V3] ❌ Error historial: {e}")
        return ""

# ============================================================================
# FUNCIÓN 3: OBTENER DATOS DEL LEAD
# ============================================================================

def obtener_datos_lead(id_lead):
    """Obtiene nombre, email, teléfono"""
    try:
        logger.info(f"[CHAT_V3] 👤 Obteniendo datos del lead...")
        
        leads_col = get_collection("leads")
        
        # Intentar con ObjectId
        try:
            lead = leads_col.find_one({"_id": ObjectId(id_lead)})
        except:
            # Si falla, intentar como string
            lead = leads_col.find_one({"_id": id_lead})
        
        if not lead:
            logger.warning(f"[CHAT_V3] ⚠️  Lead no encontrado: {id_lead}")
            return {"nombre": "Cliente", "email": "", "telefono": ""}
        
        nombre = lead.get("nombre")
        if not nombre or nombre == "Cliente":
            nombre = lead.get("telefono", "Cliente")
        
        datos = {
            "nombre": nombre if nombre else "Cliente",
            "email": lead.get("email", ""),
            "telefono": lead.get("telefono", "")
        }
        
        logger.info(f"[CHAT_V3] ✅ Datos: {datos['nombre']} ({datos['telefono']})")
        return datos
    
    except Exception as e:
        logger.error(f"[CHAT_V3] ❌ Error lead: {e}", exc_info=True)
        return {"nombre": "Cliente", "email": "", "telefono": ""}

# ============================================================================
# FUNCIÓN 4: CONSTRUIR PROMPT PARA GEMINI
# ============================================================================

def construir_prompt(id_lead, mensaje_usuario):
    """Construye prompt COMPLETO con TODO el contexto"""
    
    logger.info("[CHAT_V3] 🏗️  Construyendo prompt completo...")
    
    catalogo = obtener_catalogo_productos()
    historial = obtener_historial(id_lead, limite=10)
    datos = obtener_datos_lead(id_lead)
    
    prompt = f"""{INFO_FRESST}

{catalogo}
{historial}

👤 CONTEXTO DEL CLIENTE:
Nombre: {datos['nombre']}
Email: {datos['email']}
Teléfono: {datos['telefono']}

═══════════════════════════════════════════════════════════════════════════

🤖 INSTRUCCIONES PARA KLIOFER:

1. IDENTIDAD: Eres KLIOFER, asistente experto de FRESST
2. TONO: Profesional, amable, directo, eficiente
3. MÁXIMO: 3-4 líneas por respuesta
4. CONTEXTO: Siempre recuerda qué preguntó antes
5. PRODUCTO: Si pregunta por algo → Sugiere 2-3 opciones del catálogo
6. CONSULTAS: Si pide precio, características → Dale datos exactos
7. COMPRA: Si quiere comprar → Ofrece SOLO 2 métodos:
   ✓ Contraentrega (entrega a domicilio, pagan al recibir)
   ✓ Presencial (compran en local, pagan allá)
8. CONTRAENTREGA: Si elige → Pide dirección de entrega
9. PRESENCIAL: Si elige → Da dirección del local:
   📍 Av. Maldonado e Islas Malvinas, Quito
   ⏰ Martes-Domingo, 9AM-6PM
10. CONFIRMACIÓN: Si da dirección → Genera código y confirma todo
11. NOMBRE: Usa siempre el nombre del cliente
12. NUNCA repitas saludos
13. NUNCA olvides lo que preguntó

═══════════════════════════════════════════════════════════════════════════

📨 NUEVO MENSAJE:
{datos['nombre']}: {mensaje_usuario}

🤖 RESPUESTA DE KLIOFER (breve, natural, experto):
"""
    
    logger.info(f"[CHAT_V3] ✅ Prompt listo ({len(prompt)} chars)")
    return prompt

# ============================================================================
# FUNCIÓN 5: PROCESAR MENSAJE
# ============================================================================

def procesar_mensaje(id_lead, numero_cliente, mensaje_usuario):
    """Procesa mensaje completo con Gemini"""
    
    logger.info("=" * 80)
    logger.info(f"[CHAT_V3] 📨 PROCESANDO MENSAJE")
    logger.info(f"[CHAT_V3] 📱 De: {numero_cliente}")
    logger.info(f"[CHAT_V3] 💬 Mensaje: {mensaje_usuario[:60]}...")
    logger.info("=" * 80)
    
    try:
        datos = obtener_datos_lead(id_lead)
        logger.info(f"[CHAT_V3] 👤 Cliente: {datos['nombre']}")
        
        # Construir prompt
        prompt = construir_prompt(id_lead, mensaje_usuario)
        
        # Llamar Gemini
        logger.info("[CHAT_V3] 🤖 Llamando Gemini...")
        respuesta = get_gemini_response(prompt)
        
        logger.info(f"[CHAT_V3] ✅ Respuesta: {respuesta[:80]}...")
        logger.info("=" * 80)
        
        return {
            "success": True,
            "respuesta": respuesta,
            "nombre_cliente": datos['nombre'],
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"[CHAT_V3] ❌ ERROR: {e}", exc_info=True)
        return {
            "success": False,
            "respuesta": "Perdón, hubo un error. Intenta de nuevo.",
            "error": str(e)
        }