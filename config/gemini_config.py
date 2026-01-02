# ============================================================================
# RUTA: backend/config/gemini_config.py
# DESCRIPCIÓN: Configuración de Google Gemini API
# USO: Para generar respuestas inteligentes del bot
# ============================================================================

import os
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configurar Gemini
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    logger.info("✅ Google Gemini API configurado")
else:
    logger.warning("⚠️ GOOGLE_API_KEY no está configurado")

def get_gemini_response(prompt: str) -> str:
    """
    Obtiene respuesta de Gemini API
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=1024,
            )
        )
        return response.text
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Error en Gemini API: {error_msg}")
        
        # ← IMPRIME AQUÍ
        print(f"\n🔴 ERROR GEMINI: {error_msg}\n")
        
        # Verificar si es error de crédito
        if "resource exhausted" in error_msg.lower() or "quota" in error_msg.lower() or "429" in error_msg:
            print("⚠️  POSIBLE FALTA DE CRÉDITO O QUOTA EXCEDIDA")
            return "Lo siento, el servicio no está disponible en este momento. Intenta más tarde."
        
        return "Lo siento, hubo un error procesando tu pregunta. Intenta de nuevo."

