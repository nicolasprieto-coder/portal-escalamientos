import requests
import logging
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


def _saludo_por_hora() -> str:
    hora = datetime.now().hour
    if 5 <= hora < 12:
        return "Buenos días"
    elif 12 <= hora < 18:
        return "Buenas tardes"
    else:
        return "Buenas noches"


def generar_borrador(servicio, nombre_destinatario, hora_inicio, texto_logs, contactos, descripcion=None) -> dict:
    saludo       = _saludo_por_hora()
    destinatario = nombre_destinatario
    prompt       = _construir_prompt(saludo, destinatario, servicio, descripcion, hora_inicio, texto_logs)

    # Intento 1: Gemini
    if getattr(settings, 'GEMINI_API_KEY', ''):
        logger.info('Intentando generar borrador con Gemini...')
        resultado = _llamar_gemini(prompt)
        if not resultado.get('error'):
            logger.info('Borrador generado exitosamente con Gemini.')
            return _parsear(resultado['texto'])
        logger.warning(f'[GEMINI FALLÓ] {resultado["error"]}')
    else:
        logger.warning('[GEMINI] API key no configurada, saltando...')

    # Intento 2: Groq
    if getattr(settings, 'GROQ_API_KEY', ''):
        logger.info('Intentando generar borrador con Groq...')
        resultado = _llamar_groq(prompt)
        if not resultado.get('error'):
            logger.info('Borrador generado exitosamente con Groq.')
            return _parsear(resultado['texto'])
        logger.warning(f'[GROQ FALLÓ] {resultado["error"]}')
    else:
        logger.warning('[GROQ] API key no configurada, saltando...')

    # Intento 3: Simulado
    logger.error('[AI SERVICE] Ambas IAs fallaron — usando borrador simulado.')
    return _simulado(saludo, destinatario, servicio, descripcion, hora_inicio)


def _llamar_groq(prompt: str) -> dict:
    try:
        r = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {settings.GROQ_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'llama-3.3-70b-versatile',
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.3,
                'max_tokens': 1024,
            },
            timeout=30,
        )
        r.raise_for_status()
        texto = r.json()['choices'][0]['message']['content']
        return {'texto': texto, 'error': None}
    except Exception as e:
        return {'texto': '', 'error': str(e)}


def _llamar_gemini(prompt: str) -> dict:
    modelo = getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash')
    try:
        r = requests.post(
            f'https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={settings.GEMINI_API_KEY}',
            json={'contents': [{'parts': [{'text': prompt}]}],
                  'generationConfig': {'temperature': 0.3, 'maxOutputTokens': 1024}},
            timeout=30,
        )
        r.raise_for_status()
        texto = r.json()['candidates'][0]['content']['parts'][0]['text']
        return {'texto': texto, 'error': None}
    except Exception as e:
        return {'texto': '', 'error': str(e)}


def _construir_prompt(saludo, destinatario, servicio, descripcion, hora_inicio, logs) -> str:
    logs_resumidos = logs[:2000] if len(logs) > 2000 else logs

    return f"""Eres un redactor técnico del equipo de NOC de una empresa de telecomunicaciones.

Tu tarea es redactar un correo formal de escalamiento en español.

DATOS DE LA INCIDENCIA:
- Saludo: {saludo}
- Destinatario: {destinatario}
- Servicio afectado: {servicio}
- Hora de inicio: {hora_inicio}
- Error principal detectado: {descripcion}

LOGS RECOPILADOS:
{logs_resumidos}

INSTRUCCIONES ESTRICTAS:
- Empieza con "{saludo}" en la primera línea
- Segunda línea: "{destinatario},"
- Tercera línea en blanco
- El tono debe reflejar que es una afectación MASIVA y sostenida, no un error puntual o aislado
- Usa frases como "se están presentando de manera reiterada", "se evidencia un volumen elevado de errores", "múltiples transacciones están siendo afectadas"
- Menciona EXPLÍCITAMENTE el error detectado: "{descripcion}"
- Describe el impacto funcional sin mencionar componentes internos, pods, namespaces ni tecnologías
- Menciona que se adjuntan logs para validación
- Solicita confirmación de recepción y ETA de resolución
- Máximo 200 palabras
- Firma: "Atentamente,\\nEquipo Movii"

Responde ÚNICAMENTE en este formato (sin markdown):
ASUNTO: [ESCALAMIENTO] [asunto aquí]
CUERPO:
[cuerpo aquí]"""

def _parsear(texto: str) -> dict:
    asunto, cuerpo_lines, en_cuerpo = '', [], False
    for linea in texto.strip().split('\n'):
        if linea.startswith('ASUNTO:'):
            asunto = linea.replace('ASUNTO:', '').strip()
        elif linea.startswith('CUERPO:'):
            en_cuerpo = True
        elif en_cuerpo:
            cuerpo_lines.append(linea)
    return {'asunto': asunto, 'cuerpo': '\n'.join(cuerpo_lines).strip(), 'error': None}


def _simulado(saludo, destinatario, servicio, descripcion, hora_inicio, componentes) -> dict:
    componentes_str = ", ".join(componentes)
    asunto = f"[ESCALAMIENTO] Incidencia en {servicio} - {hora_inicio}"
    cuerpo = f"""{saludo}
{destinatario},

Por medio del presente comunicado, informamos que a partir de las {hora_inicio} se han detectado inconvenientes en el servicio de {servicio}.

{descripcion}

Los componentes involucrados son: {componentes_str}.

Se adjuntan los logs correspondientes para su análisis y validación.

Solicitamos atención prioritaria e indicar ETA de resolución. Por favor confirmar recepción.

Atentamente,
Equipo de Monitoreo"""
    return {'asunto': asunto, 'cuerpo': cuerpo, 'error': None}



# Detectar el error con IA
def analizar_logs_con_ia(texto_logs: str, servicio: str) -> str:
    """
    Usa la IA para detectar el error principal cuando la lógica
    de programación no encuentra un patrón claro.
    """
    prompt = f"""Analiza estos logs del servicio "{servicio}" y en UNA sola oración describe:
- Cuál es el error o problema principal que se está presentando
- Sin mencionar nombres de componentes internos, pods, namespaces ni tecnologías
- Desde la perspectiva del impacto funcional

LOGS:
{texto_logs[:3000]}

Responde SOLO con la descripción en una oración. Sin explicaciones adicionales."""

    if getattr(settings, 'GEMINI_API_KEY', ''):
        resultado = _llamar_gemini(prompt)
        if not resultado.get('error'):
            return resultado['texto'].strip()

    if getattr(settings, 'GROQ_API_KEY', ''):
        resultado = _llamar_groq(prompt)
        if not resultado.get('error'):
            return resultado['texto'].strip()

    return "Se detectaron errores en el servicio que requieren atención."