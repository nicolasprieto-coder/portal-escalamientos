import os, django, json
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from catalogo.models import Servicio, Componente, Contacto

with open(Path(__file__).parent / 'catalogo.json', encoding='utf-8') as f:
    data = json.load(f)

for slug, val in data.items():
    servicio, _ = Servicio.objects.get_or_create(slug=slug, defaults={'nombre': val['nombre']})

    for comp in val.get('componentes', []):
        Componente.objects.get_or_create(
            servicio=servicio,
            id_componente=comp['id'],
            defaults={
                'nombre':       comp['nombre'],
                'namespace':    comp.get('namespace', ''),
                'app_label':    comp.get('app_label', ''),
                'terminos_log': comp.get('terminos_log', []),
            }
        )

    contacto_data = val.get('contacto', {})
    if contacto_data:
        Contacto.objects.get_or_create(
            servicio=servicio,
            defaults={
                'nombre':       contacto_data.get('nombre', ''),
                'emails':       contacto_data.get('emails', []),
                'emails_copia': contacto_data.get('emails_copia', []),
                'tipo':         contacto_data.get('tipo', 'proveedor'),
            }
        )

print('Migración completada.')