from .models import Servicio, Componente, Contacto

def get_servicios_choices():
    return [(s.slug, s.nombre) for s in Servicio.objects.all()]

def get_servicio(sid: str) -> dict | None:
    try:
        s = Servicio.objects.get(slug=sid)
        return {'nombre': s.nombre, 'slug': s.slug}
    except Servicio.DoesNotExist:
        return None

def get_componentes(sid: str) -> list:
    try:
        s = Servicio.objects.get(slug=sid)
        return [{
            'id':           c.id_componente,
            'nombre':       c.nombre,
            'namespace':    c.namespace,
            'app_label':    c.app_label,
            'terminos_log': c.terminos_log,
        } for c in s.componentes.all()]
    except Servicio.DoesNotExist:
        return []

def get_contacto(sid: str) -> dict:
    try:
        s = Servicio.objects.get(slug=sid)
        c = s.contactos.first()
        if not c:
            return {}
        return {
            'nombre':       c.nombre,
            'emails':       c.emails,
            'emails_copia': c.emails_copia,
            'tipo':         c.tipo,
        }
    except Servicio.DoesNotExist:
        return {}

def get_emails(sid: str) -> list:
    return get_contacto(sid).get('emails', [])

def get_emails_copia(sid: str) -> list:
    return get_contacto(sid).get('emails_copia', [])

def get_nombre_destinatario(sid: str) -> str:
    return get_contacto(sid).get('nombre', 'Equipo de soporte')