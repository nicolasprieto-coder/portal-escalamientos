from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
import logging
logger = logging.getLogger(__name__)


from .forms import IncidenciaForm, PreviewForm
from .models import Escalamiento
from catalogo.utils import get_servicio, get_componentes, get_emails, get_emails_copia, get_nombre_destinatario
from services.grafana import get_logs_todos, a_texto
from services.ai_service import generar_borrador
from services.mail import enviar_escalamiento




import json


def inicio(request):
    return render(request, 'incidencias/inicio.html', {'form': IncidenciaForm()})


def registrar(request):
    if request.method != 'POST':
        return redirect('inicio')

    form = IncidenciaForm(request.POST)
    if not form.is_valid():
        return render(request, 'incidencias/inicio.html', {'form': form})

    sid         = form.cleaned_data['servicio']
    hora_inicio = form.cleaned_data['hora_inicio_novedad']
    termino_error    = form.cleaned_data.get('termino_error', '').strip()

    servicio_data = get_servicio(sid)
    componentes   = get_componentes(sid)
    emails        = get_emails(sid)
    emails_copia  = get_emails_copia(sid)
    nombre_dest   = get_nombre_destinatario(sid)

    # 1. Extraer logs de Grafana
    resultados = get_logs_todos(componentes, hora_inicio)
    texto_logs = a_texto(resultados)

    # 2. Detectar error principal con lógica de programación
    if termino_error:
    # Camino A: el operador especificó el error manualmente
        descripcion = termino_error
        logger.info(f'Descripción manual del operador: {descripcion}')

    else:
        # Camino B: análisis automático con lógica de programación
        from services.grafana import detectar_error_principal
        descripcion = detectar_error_principal(resultados)

        if not descripcion:
            # Camino C: la IA analiza los logs
            logger.info('Sin patrón claro — usando IA para analizar...')
            from services.ai_service import analizar_logs_con_ia
            descripcion = analizar_logs_con_ia(texto_logs, servicio_data['nombre'])

        logger.info(f'Descripción detectada automáticamente: {descripcion}')
    # 3. Si no encontró patrón claro, usar IA para analizar
    if not descripcion:
        logger.info('Sin patrón claro en logs — usando IA para analizar...')
        from services.ai_service import analizar_logs_con_ia
        descripcion = analizar_logs_con_ia(texto_logs, servicio_data['nombre'])

    logger.info(f'Descripción detectada automáticamente: {descripcion}')

    # 4. Generar borrador con Gemini/Groq
    borrador = generar_borrador(
        servicio=servicio_data['nombre'],
        nombre_destinatario=nombre_dest,
        hora_inicio=hora_inicio.strftime('%Y-%m-%d %H:%M'),
        texto_logs=texto_logs,
        contactos=[{'email': e} for e in emails],
        descripcion=descripcion,
    )

    # 5. Guardar
    esc = Escalamiento.objects.create(
        servicio_id=sid,
        servicio_nombre=servicio_data['nombre'],
        descripcion=descripcion,
        hora_inicio_novedad=hora_inicio,
        componentes_afectados=[c['nombre'] for c in componentes],
        destinatarios=emails,
        destinatarios_copia=emails_copia,
        asunto_correo=borrador['asunto'],
        cuerpo_correo=borrador['cuerpo'],
        logs_recopilados=texto_logs,
    )
    return redirect('previsualizar', pk=esc.pk)

def previsualizar(request, pk):
    esc = get_object_or_404(Escalamiento, pk=pk)
    
    if request.method == 'POST':
        form = PreviewForm(request.POST)
        if form.is_valid():
            asunto       = form.cleaned_data['asunto']
            cuerpo       = form.cleaned_data['cuerpo']
            destinatarios = [d.strip() for d in form.cleaned_data['destinatarios'].splitlines() if d.strip()]
            copia_raw     = request.POST.get('destinatarios_copia', '')
            copia         = [d.strip() for d in copia_raw.split('\n') if d.strip()]

            resultado = enviar_escalamiento(
                destinatarios=destinatarios,
                copia=copia,
                asunto=asunto,
                cuerpo=cuerpo,
                texto_logs=esc.logs_recopilados,
                servicio=esc.servicio_nombre,
                hora_inicio=esc.hora_inicio_novedad,
            )
            esc.destinatarios_copia = copia
            esc.save()
            if resultado['ok']:
                esc.asunto_correo = asunto
                esc.cuerpo_correo = cuerpo
                esc.destinatarios = destinatarios
                esc.estado        = 'enviado'
                esc.enviado_en    = timezone.now()
                esc.save()
                messages.success(request, f"Escalamiento enviado a {', '.join(destinatarios)}")
                return redirect('historial')
            else:
                messages.error(request, f"Error al enviar: {resultado['error']}")

    form = PreviewForm(initial={
        'escalamiento_id': esc.pk,
        'asunto':          esc.asunto_correo,
        'cuerpo':          esc.cuerpo_correo,
        'destinatarios':   '\n'.join(esc.destinatarios),
    })
    return render(request, 'incidencias/previsualizar.html', {
    'form': form,
    'esc': esc,
    'destinatarios_iniciales': json.dumps(esc.destinatarios),
    'copia_iniciales':         json.dumps(esc.destinatarios_copia),
})


def historial(request):
    escalamientos = Escalamiento.objects.all()

    # Agregar conteo de mensajes no vistos a cada escalamiento
    for esc in escalamientos:
        esc.mensajes_nuevos = esc.mensajes.filter(visto=False).count()

    return render(request, 'incidencias/historial.html', {
        'escalamientos': escalamientos
    })

def eliminar(request, pk):
    if request.method == 'POST':
        esc = get_object_or_404(Escalamiento, pk=pk)
        esc.delete()
        messages.success(request, f'Escalamiento #{pk} eliminado correctamente.')
    return redirect('historial')

def info_servicio(request, sid):
    from django.http import JsonResponse
    from catalogo.utils import get_componentes, get_contacto
    contacto = get_contacto(sid)
    return JsonResponse({
        'componentes': get_componentes(sid),
        'contacto': contacto,
    })


## Funcionalidad para leer la traza de los correos

from services.gmail_reader import buscar_respuestas

def detalle(request, pk):
    esc = get_object_or_404(Escalamiento, pk=pk)

    # Marcar mensajes como vistos
    esc.mensajes.filter(visto=False).update(visto=True)

    respuestas = []
    if esc.estado == 'enviado' and esc.asunto_correo:
        respuestas = buscar_respuestas(esc.asunto_correo, esc.enviado_en)

    return render(request, 'incidencias/detalle.html', {
        'esc':        esc,
        'respuestas': respuestas,
    })


def cerrar_escalamiento(request, pk):
    if request.method == 'POST':
        esc            = get_object_or_404(Escalamiento, pk=pk)
        esc.estado     = 'cerrado'
        esc.save()
        messages.success(request, f'Escalamiento #{pk} cerrado correctamente.')
    return redirect('detalle', pk=pk)


## Funcionalidad para notificar


from django.http import JsonResponse
from django.utils import timezone
from .models import Escalamiento, MensajeNotificado

def check_respuestas(request):
    from services.gmail_reader import buscar_respuestas

    enviados = Escalamiento.objects.filter(estado='enviado')
    nuevas   = []

    for esc in enviados:
        if not esc.enviado_en:
            continue

        respuestas = buscar_respuestas(esc.asunto_correo, esc.enviado_en)

        for r in respuestas:
            # Si ya está en BD, ignorar
            if MensajeNotificado.objects.filter(mensaje_id=r['mensaje_id']).exists():
                continue

            # Es nuevo — guardar y notificar
            MensajeNotificado.objects.create(
                mensaje_id=r['mensaje_id'],
                escalamiento=esc,
                remitente=r['remitente'],
            )
            nuevas.append({
                'mensaje_id':      r['mensaje_id'],
                'escalamiento_id': esc.pk,
                'servicio':        esc.servicio_nombre,
                'remitente':       r['remitente'],
                'fecha':           r['fecha'],
            })

    return JsonResponse({'respuestas': nuevas})



# Home / Dashboard

def dashboard(request):
    from django.db.models import Count, ExpressionWrapper, F, DurationField
    from django.utils import timezone
    from datetime import timedelta
    import json

    total      = Escalamiento.objects.count()
    abiertos   = Escalamiento.objects.filter(estado='enviado').count()
    cerrados   = Escalamiento.objects.filter(estado='cerrado').count()
    borradores = Escalamiento.objects.filter(estado='borrador').count()
    enviados   = abiertos

    tiempos = Escalamiento.objects.filter(
        estado='cerrado', enviado_en__isnull=False
    ).annotate(
        duracion=ExpressionWrapper(
            F('enviado_en') - F('creado_en'),
            output_field=DurationField()
        )
    ).values_list('duracion', flat=True)

    if tiempos:
        total_segundos = sum(t.total_seconds() for t in tiempos if t)
        promedio_horas = round(total_segundos / len(tiempos) / 3600, 1)
        tiempo_promedio = f"{promedio_horas}h"
    else:
        tiempo_promedio = "—"

    servicios_qs = (
        Escalamiento.objects
        .values('servicio_nombre')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )
    servicios_labels = [s['servicio_nombre'] for s in servicios_qs]
    servicios_data   = [s['total'] for s in servicios_qs]

    MESES_ES = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    meses_labels, meses_data = [], []
    hoy = timezone.now()
    for i in range(5, -1, -1):
        fecha = hoy - timedelta(days=30 * i)
        count = Escalamiento.objects.filter(
            creado_en__year=fecha.year,
            creado_en__month=fecha.month
        ).count()
        meses_labels.append(MESES_ES[fecha.month - 1])
        meses_data.append(count)

    apilado_enviados, apilado_cerrados, apilado_borradores = [], [], []
    for nombre in servicios_labels:
        qs = Escalamiento.objects.filter(servicio_nombre=nombre)
        apilado_enviados.append(qs.filter(estado='enviado').count())
        apilado_cerrados.append(qs.filter(estado='cerrado').count())
        apilado_borradores.append(qs.filter(estado='borrador').count())

    ultimos = Escalamiento.objects.order_by('-creado_en')[:5]

    return render(request, 'incidencias/dashboard.html', {
        'total':              total,
        'abiertos':           abiertos,
        'cerrados':           cerrados,
        'borradores':         borradores,
        'enviados':           enviados,
        'tiempo_promedio':    tiempo_promedio,
        'servicios_labels':   json.dumps(servicios_labels),
        'servicios_data':     json.dumps(servicios_data),
        'meses_labels':       json.dumps(meses_labels),
        'meses_data':         json.dumps(meses_data),
        'apilado_enviados':   json.dumps(apilado_enviados),
        'apilado_cerrados':   json.dumps(apilado_cerrados),
        'apilado_borradores': json.dumps(apilado_borradores),
        'ultimos':            ultimos,
    })