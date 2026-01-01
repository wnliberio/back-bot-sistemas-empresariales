# ============================================================================
# RUTA: backend/services/chat_service.py - VERSION 2.0
# DESCRIPCIÓN: Servicio de Chat - AHORA CON HISTORIAL COMPLETO
# USO: Procesar mensajes con contexto de conversación anterior
# ============================================================================

import logging
from config.gemini_config import get_gemini_response
from services.sales_flow_service import extraer_datos_del_mensaje, detectar_etapa_compra
from datetime import datetime

logger = logging.getLogger(__name__)

# ============================================================================
# PROMPT DEL SISTEMA - KLIOFER
# ============================================================================

PROMPT_SISTEMA = """🤖 KLIOFER - ASISTENTE EXPERTO DE FRESST

Eres Kliofer, el asistente de ventas experto de FRESST, líder en equipamiento profesional 
para negocios gastronómicos y comerciales.

═══════════════════════════════════════════════════════════════════════════════
SOBRE FRESST - LA EMPRESA
═══════════════════════════════════════════════════════════════════════════════
✅ MISIÓN: Proporcionar soluciones completas de equipamiento profesional
✅ UBICACIÓN: Av. Maldonado e Islas Malvinas, Quito
✅ HORARIO: Martes a Domingo, 9AM - 6PM
✅ ENTREGA: 2-3 días hábiles en toda la ciudad
✅ GARANTÍA: Completa en todos los productos (1.5 a 2 años según producto)
✅ FORMAS DE COMPRA: Contraentrega (a domicilio) o Presencial (en local)

═══════════════════════════════════════════════════════════════════════════════
CATÁLOGO COMPLETO DE PRODUCTOS
═══════════════════════════════════════════════════════════════════════════════

🧊 REFRIGERACIÓN:
├─ Frigoríficos: $1,200-2,500 (Múltiples modelos)
├─ Vitrinas Horizontales: $1,800-2,000 (Ideal panaderías)
├─ Vitrinas Verticales: $1,500-2,100 (Mayor accesibilidad)
├─ Vitrinas con/sin Caja: $1,600-2,200
└─ Bomboneras: $800-1,500 (Para mostrador)

🔥 COCCIÓN:
├─ Hornos Industriales: $2,800-3,500 (Gas/Eléctrico)
├─ Freidoras Profesionales: $1,500-2,200 (Doble 40L)
├─ Cocinas Industriales: $2,000-2,800 (4-6 quemadores)
├─ Asaderos Profesionales: $2,500-4,000 (Parrilla giratoria)
└─ Salchipaperas: $1,200-1,800 (Para quioscos)

🪑 MOBILIARIO:
├─ Mesas Acero Inoxidable: $600-900
├─ Estanterías Metálicas: $400-600 (Muy económicas)
├─ Góndolas Exhibición: $1,200-1,500 (Modernas)
└─ Paneras Madera: $350-500 (Rústicas)

⚙️ EQUIPOS ESPECIALES:
├─ Carro Hotdogs Profesional: $1,500-2,000 (Móvil)
├─ Balanza Mecánica: $250-300 (Confiable)
└─ Balanza Digital: $450-600 (Exacta)

═══════════════════════════════════════════════════════════════════════════════
OBJETIVO PRINCIPAL
═══════════════════════════════════════════════════════════════════════════════
1. Ayudar al cliente a encontrar EL PRODUCTO PERFECTO
2. Hacer que se sienta escuchado y entendido
3. Guiar NATURALMENTE hacia la compra
4. Cerrar venta con: CONTRAENTREGA o PRESENCIAL
5. NUNCA repetir información ya dada
6. RECORDAR TODO lo que el cliente preguntó antes

═══════════════════════════════════════════════════════════════════════════════
REGLAS CRÍTICAS DE CONVERSACIÓN
═══════════════════════════════════════════════════════════════════════════════
1. ⚠️ LEE EL HISTORIAL PRIMERO - Evita repetir saludos
2. ⚠️ RESPETA EL CONTEXTO - Si preguntó un producto, mantén ese tema
3. ⚠️ SÉ NATURAL - No robótico, conversacional, amigable
4. ⚠️ BREVE - Máximo 3-4 líneas por respuesta
5. ⚠️ EXPERTO - Conoce TODOS los productos y precios
6. ⚠️ PERSONALIZADO - Usa el nombre si lo mencionó
7. ⚠️ CIERRE DE VENTA - "¿Cómo deseas pagar: contraentrega o presencial?"

═══════════════════════════════════════════════════════════════════════════════
TONO Y ESTILO
═══════════════════════════════════════════════════════════════════════════════
✅ Profesional pero amigable
✅ Experto en productos FRESST
✅ Directo al grano
✅ Respuestas cortas y claras
❌ NO robótico
❌ NO genérico
❌ NO repetitivo
❌ NO saludos múltiples
"""


# ============================================================================
# FUNCIONES DE CONSTRUCCIÓN DE CONTEXTO
# ============================================================================

def construir_historial_formateado(historial: list) -> str:
    """
    Construye un string con el historial formateado para Gemini
    """
    if not historial:
        return "⚠️ Esta es la PRIMERA vez que habla este cliente.\n"
    
    contexto = "📜 HISTORIAL DE CONVERSACIÓN ACTUAL:\n"
    contexto += "=" * 70 + "\n"
    
    # Últimos 15 mensajes para no saturar el contexto
    for msg in historial[-15:]:
        emisor = msg.get("emisor", "desconocido").upper()
        texto = msg.get("texto", "")
        
        if emisor == "CLIENTE":
            contexto += f"👤 Cliente: {texto}\n"
        elif emisor == "BOT":
            contexto += f"🤖 Kliofer: {texto}\n"
    
    contexto += "=" * 70 + "\n"
    return contexto


def construir_instrucciones_contexto(historial: list, etapa: str) -> str:
    """
    Construye instrucciones específicas según la etapa de venta
    """
    instrucciones = "\n═══════════════════════════════════════════════════════════════════════════════\n"
    instrucciones += "INSTRUCCIONES PARA ESTA RESPUESTA\n"
    instrucciones += "═══════════════════════════════════════════════════════════════════════════════\n"
    
    if etapa == "consulta":
        instrucciones += """
ETAPA: Cliente consultando (sin decisión clara)
- Responde la pregunta DIRECTAMENTE
- Ofrece información útil
- Sugiere alternativas si es apropiado
- Máximo 3 líneas
"""
    
    elif etapa == "intención_clara":
        instrucciones += """
ETAPA: Cliente dijo que quiere comprar
- CONFIRMA: Producto + Precio exacto
- Pregunta: "¿Cómo deseas: contraentrega (a domicilio) o presencial (en local)?"
- Sé claro, sin confusiones
- Máximo 3 líneas
"""
    
    elif etapa == "esperando_metodo":
        instrucciones += """
ETAPA: Cliente no eligió método de entrega
- Pregunta NUEVAMENTE cual método prefiere:
  "¿Prefieres contraentrega (te lo llevamos) o presencial (en nuestro local)?"
- Ofrece ambas opciones CLARAMENTE
- 2-3 líneas
"""
    
    elif etapa == "direccion_contraentrega":
        instrucciones += """
ETAPA: Cliente eligió CONTRAENTREGA
- Pide la dirección: "¿Cuál es tu dirección de entrega?"
- Dile: "Entrega en 2-3 días hábiles"
- Dile: "Te llamaremos para coordinar"
- NO pidas datos innecesarios
- 2-3 líneas
"""
    
    elif etapa == "presencial_confirmado":
        instrucciones += """
ETAPA: Cliente va al LOCAL
- Confirma horarios y ubicación
- Breve y directo
- 2 líneas máximo
"""
    
    elif etapa == "venta_completada":
        instrucciones += """
ETAPA: VENTA COMPLETADA
- Confirma resumen final
- Agradece profesionalmente
- Ofrece soporte post-venta
- 3-4 líneas
"""
    
    else:
        instrucciones += """
ETAPA: Desconocida (Sé profesional y amable)
- Responde naturalmente
- Guía hacia un cierre
- Máximo 3 líneas
"""
    
    instrucciones += "\n"
    return instrucciones


# ============================================================================
# FUNCIÓN PRINCIPAL DE PROCESAMIENTO
# ============================================================================

def procesar_mensaje(
    texto_usuario: str,
    historial: list = None,
    datos_lead: dict = None
) -> dict:
    """
    Procesa un mensaje completo CON HISTORIAL
    
    Args:
        texto_usuario: El nuevo mensaje del cliente
        historial: Lista de mensajes previos (para contexto)
        datos_lead: Datos del cliente (nombre, teléfono, etc)
    
    Returns:
        dict con respuesta de Gemini + metadata
    """
    
    try:
        if historial is None:
            historial = []
        
        logger.info(f"🔄 Procesando mensaje con {len(historial)} mensajes en historial")
        
        # ================================================
        # 1️⃣ EXTRAER DATOS DEL MENSAJE
        # ================================================
        datos_extraidos = extraer_datos_del_mensaje(texto_usuario)
        nombre_cliente = None
        
        if datos_lead and isinstance(datos_lead, dict):
            nombre_cliente = datos_lead.get("nombre")
        
        if not nombre_cliente and datos_extraidos.get("nombre"):
            nombre_cliente = datos_extraidos["nombre"]
        
        logger.info(f"👤 Cliente: {nombre_cliente or 'Desconocido'}")
        logger.info(f"📝 Datos extraidos: {datos_extraidos}")
        
        # ================================================
        # 2️⃣ DETECTAR ETAPA DE VENTA
        # ================================================
        etapa = detectar_etapa_compra(historial)
        logger.info(f"📊 Etapa detectada: {etapa}")
        
        # ================================================
        # 3️⃣ CONSTRUIR CONTEXTO COMPLETO
        # ================================================
        historial_str = construir_historial_formateado(historial)
        instrucciones_etapa = construir_instrucciones_contexto(historial, etapa)
        
        # ================================================
        # 4️⃣ CONSTRUIR PROMPT FINAL PARA GEMINI
        # ================================================
        prompt_final = f"""{PROMPT_SISTEMA}

{historial_str}

{instrucciones_etapa}

📨 NUEVO MENSAJE DEL CLIENTE:
{texto_usuario}

🤖 Tu respuesta como Kliofer (natural, breve, experto):
"""
        
        logger.info(f"📤 Enviando a Gemini...")
        logger.info(f"   Etapa: {etapa}")
        logger.info(f"   Historial: {len(historial)} mensajes")
        
        # ================================================
        # 5️⃣ OBTENER RESPUESTA DE GEMINI
        # ================================================
        respuesta = get_gemini_response(prompt_final)
        
        logger.info(f"✅ Respuesta generada ({len(respuesta)} caracteres)")
        
        return {
            "success": True,
            "respuesta": respuesta,
            "datos_extraidos": datos_extraidos,
            "etapa": etapa,
            "nombre_cliente": nombre_cliente,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"❌ Error procesando mensaje: {e}", exc_info=True)
        return {
            "success": False,
            "respuesta": "Lo siento, hubo un error procesando tu mensaje. Intenta de nuevo.",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def generar_saludo(nombre_cliente: str = None) -> str:
    """Genera saludo personalizado (solo para primera vez)"""
    if nombre_cliente:
        return f"¡Hola {nombre_cliente}! Soy Kliofer de FRESST. ¿Qué equipamiento profesional necesitas?"
    else:
        return "¡Hola! Soy Kliofer de FRESST. ¿Qué equipamiento profesional necesitas?"