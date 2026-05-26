import requests
import logging
from datetime import datetime, timedelta, timezone
from django.conf import settings

logger = logging.getLogger(__name__)


def get_logs(componente: dict, hora_inicio: datetime) -> dict:
    if not settings.GRAFANA_TOKEN:
        logger.warning('GRAFANA_TOKEN no configurado — usando logs simulados.')
        return _simulado(componente)

    if hora_inicio.tzinfo is None:
        hora_inicio = hora_inicio.replace(tzinfo=timezone.utc)

    desde = hora_inicio
    hasta = datetime.now(tz=timezone.utc)

    query_lucene = _construir_query(componente, desde, hasta)

    url = (
        f"{settings.GRAFANA_URL}/api/datasources/proxy/"
        f"{settings.GRAFANA_DATASOURCE_ID}/oke-*/_search"
    )
    headers = {'Authorization': f'Bearer {settings.GRAFANA_TOKEN}'}
    params  = {'q': query_lucene, 'size': 100, 'sort': '@timestamp:asc'}

    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        lineas = _parsear(r.json())
        return {'componente': componente['nombre'], 'logs': lineas, 'error': None}

    except requests.RequestException as e:
        logger.error(f"Error consultando Grafana para {componente['id']}: {e}")
        return {'componente': componente['nombre'], 'logs': [], 'error': str(e)}


def _construir_query(componente: dict, desde: datetime, hasta: datetime) -> str:
    desde_str = desde.strftime('%Y-%m-%dT%H:%M:%SZ')
    hasta_str = hasta.strftime('%Y-%m-%dT%H:%M:%SZ')

    partes = []

    # Filtro por namespace
    if componente.get('namespace'):
        partes.append(f'kubernetes.namespace_name:"{componente["namespace"]}"')

    # Filtro por app label
    if componente.get('app_label'):
        partes.append(f'kubernetes.labels.app:"{componente["app_label"]}"')

    # Términos adicionales del catálogo (opcionales)
    for termino in componente.get('terminos_log', []):
        partes.append(f'logs:"{termino}"')

    # Filtrar solo errores — busca cualquiera de estas palabras en el campo logs
    partes.append('(logs:"ERROR" OR logs:"WARN" OR logs:"FAIL" OR logs:"Exception" OR logs:"error" OR logs:"exception")')

    # Ventana de tiempo
    partes.append(f'@timestamp:[{desde_str} TO {hasta_str}]')

    return ' AND '.join(partes)


def _parsear(data: dict) -> list[str]:
    lineas = []
    hits   = data.get('hits', {}).get('hits', [])

    for hit in hits:
        source = hit.get('_source', {})
        k8s    = source.get('kubernetes', {})

        # Timestamp
        ts_raw = source.get('@timestamp', '')
        try:
            ts_dt  = datetime.fromisoformat(ts_raw.replace('Z', '+00:00'))
            ts_str = ts_dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            ts_str = ts_raw

        pod       = k8s.get('pod_name', '')
        namespace = k8s.get('namespace_name', '')
        mensaje   = source.get('logs', '')

        # Limpiar el prefijo de timestamp que viene dentro del campo logs
        # Formato: "2026-04-30T01:10:01.727954218+00:00 stdout F [mensaje real]"
        if ' stdout F ' in mensaje:
            mensaje = mensaje.split(' stdout F ', 1)[-1].strip()
        elif ' stderr F ' in mensaje:
            mensaje = mensaje.split(' stderr F ', 1)[-1].strip()

        lineas.append(f"[{ts_str}] [{namespace}/{pod}] {mensaje}")

    return lineas


def get_logs_todos(componentes: list, hora_inicio: datetime) -> list[dict]:
    return [get_logs(c, hora_inicio) for c in componentes]


def a_texto(resultados: list[dict]) -> str:
    bloques = ["=" * 60, "LOGS DE INCIDENCIA", "=" * 60, ""]
    for r in resultados:
        bloques.append(f"--- {r['componente'].upper()} ---")
        if r.get('error'):
            bloques.append(f"[ERROR]: {r['error']}")
        elif not r['logs']:
            bloques.append("[Sin logs en el período consultado]")
        else:
            bloques.extend(r['logs'])
        bloques.append("")
    return "\n".join(bloques)


def _simulado(componente: dict) -> dict:
    nombre = componente['nombre']
    return {
        'componente': nombre,
        'logs': [
            f"[SIMULADO] ERROR {nombre}: Connection timeout",
            f"[SIMULADO] ERROR {nombre}: HTTP 503 Service Unavailable",
        ],
        'error': None,
    }



# Aqui detectamos el error que más se repita

def detectar_error_principal(resultados: list[dict], umbral: float = 0.6) -> str:
    import re
    from collections import Counter

    KEYWORDS_ERROR = ['ERROR', 'WARN', 'FAIL', 'Exception', 'error', 'exception',
                      'timeout', 'Timeout', 'refused', 'unavailable', 'Unavailable']

    lineas_error = []
    for resultado in resultados:
        for linea in resultado.get('logs', []):
            if any(k in linea for k in KEYWORDS_ERROR):
                lineas_error.append(linea)

    if not lineas_error:
        return None

    patrones = []
    for linea in lineas_error:
        excepciones = re.findall(r'[\w]+(?:Exception|Error|Timeout|Refused)\b', linea)
        patrones.extend(excepciones)

        codigos = re.findall(r'HTTP [45]\d{2}|[45]\d{2} [A-Z][a-z]+', linea)
        patrones.extend(codigos)

        mensajes = re.findall(r'(?:message|msg|error)[\s:]+["\']?([^"\'{\n]{10,60})', linea, re.IGNORECASE)
        patrones.extend(mensajes)

    if not patrones:
        return None

    conteo = Counter(patrones)
    patron_top, frecuencia_top = conteo.most_common(1)[0]
    porcentaje = frecuencia_top / len(lineas_error)

    # Siempre retorna el más frecuente — con o sin umbral
    if porcentaje >= umbral:
        return f"{patron_top} (presente en el {round(porcentaje * 100)}% de los errores)"
    else:
        # Retorna solo el más frecuente aunque no domine
        return f"{patron_top}"