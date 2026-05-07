import json
from pathlib import Path

_PATH = Path(__file__).resolve().parent.parent / 'catalogo.json'

def cargar_catalogo():
    with open(_PATH, encoding='utf-8') as f:
        return json.load(f)

def get_servicios_choices():
    return [(k, v['nombre']) for k, v in cargar_catalogo().items()]

def get_servicio(sid):
    return cargar_catalogo().get(sid)

def get_componentes(sid):
    s = get_servicio(sid)
    return s['componentes'] if s else []

def get_contacto(sid: str) -> dict:
    s = get_servicio(sid)
    return s.get('contacto', {}) if s else {}

def get_emails(sid: str) -> list:
    contacto = get_contacto(sid)
    return contacto.get('emails', [])

def get_nombre_destinatario(sid: str) -> str:
    contacto = get_contacto(sid)
    return contacto.get('nombre', 'Equipo de soporte')

def get_emails_copia(sid: str) -> list:
    contacto = get_contacto(sid)
    return contacto.get('emails_copia', [])