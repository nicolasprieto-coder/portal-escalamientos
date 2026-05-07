import logging
from django.core.mail import EmailMessage
from django.conf import settings

logger = logging.getLogger(__name__)

def enviar_escalamiento(destinatarios, asunto, cuerpo, texto_logs, servicio, hora_inicio, copia=None) -> dict:
    try:
        nombre_adjunto = f"logs_{servicio.lower().replace(' ','_')}_{hora_inicio:%Y%m%d_%H%M}.txt"

        email = EmailMessage(
            subject=asunto,
            body=_html_template(cuerpo, servicio, hora_inicio, nombre_adjunto),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=destinatarios,
            cc=copia or [],      # ← nuevo
        )
        email.content_subtype = 'html'
        email.attach(nombre_adjunto, texto_logs.encode('utf-8'), 'text/plain')
        email.send(fail_silently=False)
        return {'ok': True, 'error': None}

    except Exception as e:
        return {'ok': False, 'error': str(e)}


def _html_template(cuerpo: str, servicio: str, hora_inicio, nombre_adjunto: str) -> str:
    # Convertir saltos de línea del cuerpo a párrafos HTML
    parrafos = ''.join(
        f'<p style="font-size:14px;color:#444444;line-height:1.7;margin:0 0 16px 0;">{linea}</p>'
        for linea in cuerpo.split('\n') if linea.strip()
    )
    hora_str = hora_inicio.strftime('%Y-%m-%d %H:%M') if hasattr(hora_inicio, 'strftime') else str(hora_inicio)

    return f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:24px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;">

  <!-- Header -->
  <tr><td style="background:#CC0000;padding:28px 32px;">
    <table width="100%"><tr>
      <td><div style="color:#fff;font-size:22px;font-weight:700;letter-spacing:1px;">MOVii</div>
          <div style="color:rgba(255,255,255,0.75);font-size:11px;letter-spacing:2px;">RED</div></td>
      <td align="right"><span style="background:rgba(255,255,255,0.15);border-radius:6px;padding:6px 14px;color:#fff;font-size:11px;font-weight:600;letter-spacing:1px;">ESCALAMIENTO</span></td>
    </tr></table>
  </td></tr>

  <!-- Alerta banner -->
  <tr><td style="background:#fff3f3;border-left:4px solid #CC0000;padding:14px 32px;">
    <span style="font-size:13px;color:#CC0000;font-weight:600;">&#9679; Incidencia activa — Requiere atención prioritaria</span>
  </td></tr>

  <!-- Body -->
  <tr><td style="padding:32px;">
    {parrafos}

    <!-- Info card -->
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#fafafa;border:1px solid #e8e8e8;border-radius:8px;padding:20px 24px;margin-bottom:32px;">
      <tr><td colspan="2" style="font-size:11px;font-weight:700;color:#999;letter-spacing:1.5px;padding-bottom:14px;">DETALLES DE LA INCIDENCIA</td></tr>
      <tr>
        <td style="font-size:13px;color:#888;padding:6px 0;width:40%;">Servicio afectado</td>
        <td style="font-size:13px;color:#2D2D2D;font-weight:600;padding:6px 0;">{servicio}</td>
      </tr>
      <tr>
        <td style="font-size:13px;color:#888;padding:6px 0;border-top:1px solid #f0f0f0;">Hora de inicio</td>
        <td style="font-size:13px;color:#2D2D2D;font-weight:600;padding:6px 0;border-top:1px solid #f0f0f0;">{hora_str}</td>
      </tr>
      <tr>
        <td style="font-size:13px;color:#888;padding:6px 0;border-top:1px solid #f0f0f0;">Estado</td>
        <td style="padding:6px 0;border-top:1px solid #f0f0f0;"><span style="background:#fff3f3;color:#CC0000;font-size:11px;font-weight:700;padding:3px 10px;border-radius:20px;">EN ESCALAMIENTO</span></td>
      </tr>
      <tr>
        <td style="font-size:13px;color:#888;padding:6px 0;border-top:1px solid #f0f0f0;">Logs adjuntos</td>
        <td style="font-size:13px;color:#2D2D2D;font-weight:600;padding:6px 0;border-top:1px solid #f0f0f0;">{nombre_adjunto}</td>
      </tr>
    </table>

    <!-- Firma -->
    <table cellpadding="0" cellspacing="0" style="border-top:1px solid #f0f0f0;padding-top:24px;width:100%;">
      <tr>
        <td width="56">
          <div style="width:40px;height:40px;border-radius:50%;background:#CC0000;text-align:center;line-height:40px;">
            <span style="color:#fff;font-size:13px;font-weight:700;">N</span>
          </div>
        </td>
        <td>
          <div style="font-size:13px;font-weight:600;color:#2D2D2D;">Equipo de Monitoreo</div>
          <div style="font-size:12px;color:#888;margin-top:2px;">MOVii RED · Gestión de Incidencias</div>
        </td>
      </tr>
    </table>
  </td></tr>

  <!-- Footer -->
  <tr><td style="background:#2D2D2D;padding:20px 32px;text-align:center;">
    <p style="font-size:11px;color:rgba(255,255,255,0.5);margin:0;line-height:1.6;">
      Este correo fue generado por el Portal de Escalamientos.<br>
      Por favor responda a este mensaje directamente.
    </p>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""