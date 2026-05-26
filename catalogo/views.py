from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Servicio, Componente, Contacto
from .forms import ServicioForm


def lista_servicios(request):
    servicios = Servicio.objects.prefetch_related('componentes', 'contactos').all()
    return render(request, 'catalogo/lista.html', {'servicios': servicios})


def _guardar_componentes_y_contacto(request, servicio):
    """Procesa y guarda componentes y contacto desde el formulario dinámico."""

    # ── Componentes ──
    nombres        = request.POST.getlist('comp_nombre[]')
    namespaces     = request.POST.getlist('comp_namespace[]')
    terminos_list  = request.POST.getlist('comp_terminos[]')
    pks_existentes = request.POST.getlist('comp_id[]')

    # Eliminar componentes que ya no están
    pks_validos = [int(pk) for pk in pks_existentes if pk]
    servicio.componentes.exclude(pk__in=pks_validos).delete()

    for i, nombre in enumerate(nombres):
        if not nombre.strip():
            continue
        terminos   = [t.strip() for t in terminos_list[i].split(',') if t.strip()] if i < len(terminos_list) else []
        namespace  = namespaces[i].strip() if i < len(namespaces) else ''
        # id y app_label se derivan del nombre automáticamente
        app_label  = nombre.strip()
        id_comp    = nombre.strip()
        pk         = int(pks_existentes[i]) if i < len(pks_existentes) and pks_existentes[i] else None

        if pk:
            comp = Componente.objects.filter(pk=pk, servicio=servicio).first()
            if comp:
                comp.nombre        = nombre.strip()
                comp.id_componente = id_comp
                comp.namespace     = namespace
                comp.app_label     = app_label
                comp.terminos_log  = terminos
                comp.save()
        else:
            Componente.objects.create(
                servicio=servicio,
                nombre=nombre.strip(),
                id_componente=id_comp,
                namespace=namespace,
                app_label=app_label,
                terminos_log=terminos,
            )

    # ── Contacto ──
    contacto_nombre      = request.POST.get('contacto_nombre', '').strip()
    contacto_tipo        = request.POST.get('contacto_tipo', 'proveedor')
    emails_raw       = request.POST.get('contacto_emails', '[]')
    emails_copia_raw = request.POST.get('contacto_emails_copia', '[]')


    emails       = [e.strip() for e in emails_raw.splitlines() if e.strip()]
    emails_copia = [e.strip() for e in emails_copia_raw.splitlines() if e.strip()]

    contacto = servicio.contactos.first()
    if contacto:
        contacto.nombre       = contacto_nombre
        contacto.tipo         = contacto_tipo
        contacto.emails       = emails
        contacto.emails_copia = emails_copia
        contacto.save()
    else:
        Contacto.objects.create(
            servicio=servicio,
            nombre=contacto_nombre,
            tipo=contacto_tipo,
            emails=emails,
            emails_copia=emails_copia,
        )


def crear_servicio(request):
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            servicio = form.save()
            _guardar_componentes_y_contacto(request, servicio)
            messages.success(request, f'Servicio "{servicio.nombre}" creado correctamente.')
            return redirect('lista_servicios')
    else:
        form = ServicioForm()
    return render(request, 'catalogo/form_servicio.html', {
        'form':   form,
        'titulo': 'Nuevo servicio',
    })


def editar_servicio(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        if form.is_valid():
            servicio = form.save()
            _guardar_componentes_y_contacto(request, servicio)
            messages.success(request, f'Servicio "{servicio.nombre}" actualizado correctamente.')
            return redirect('lista_servicios')
    else:
        form = ServicioForm(instance=servicio)
    return render(request, 'catalogo/form_servicio.html', {
        'form':     form,
        'titulo':   'Editar servicio',
        'servicio': servicio,
    })


def eliminar_servicio(request, pk):
    if request.method == 'POST':
        servicio = get_object_or_404(Servicio, pk=pk)
        nombre   = servicio.nombre
        servicio.delete()
        messages.success(request, f'Servicio "{nombre}" eliminado correctamente.')
    return redirect('lista_servicios')