from django.db import models

class Escalamiento(models.Model):
    ESTADOS = [('borrador','Borrador'), ('enviado','Enviado'), ('cerrado','Cerrado')]

    servicio_id          = models.CharField(max_length=100)
    servicio_nombre      = models.CharField(max_length=200)
    descripcion          = models.TextField()
    hora_inicio_novedad  = models.DateTimeField()
    componentes_afectados = models.JSONField(default=list)
    destinatarios        = models.JSONField(default=list)
    destinatarios_copia = models.JSONField(default=list) 
    asunto_correo        = models.CharField(max_length=300, blank=True)
    cuerpo_correo        = models.TextField(blank=True)
    logs_recopilados     = models.TextField(blank=True)
    estado               = models.CharField(max_length=20, choices=ESTADOS, default='borrador')
    creado_en            = models.DateTimeField(auto_now_add=True)
    enviado_en           = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creado_en']

    def __str__(self):
        return f"[{self.estado}] {self.servicio_nombre} - {self.hora_inicio_novedad:%Y-%m-%d %H:%M}"
    

class MensajeNotificado(models.Model):
    mensaje_id   = models.CharField(max_length=200, unique=True)
    escalamiento = models.ForeignKey(Escalamiento, on_delete=models.CASCADE, related_name='mensajes')  # ← este
    remitente    = models.CharField(max_length=200)
    visto        = models.BooleanField(default=False)
    creado_en    = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-creado_en']