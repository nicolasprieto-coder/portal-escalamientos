from django.db import models

class Servicio(models.Model):
    slug   = models.SlugField(max_length=100, unique=True)
    nombre = models.CharField(max_length=200)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Componente(models.Model):
    servicio       = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='componentes')
    id_componente  = models.CharField(max_length=200)
    nombre         = models.CharField(max_length=200)
    namespace      = models.CharField(max_length=200)
    app_label      = models.CharField(max_length=200)
    terminos_log   = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.nombre


class Contacto(models.Model):
    servicio        = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='contactos')
    nombre          = models.CharField(max_length=200)
    emails          = models.JSONField(default=list)
    emails_copia    = models.JSONField(default=list, blank=True)
    tipo            = models.CharField(max_length=50, default='proveedor')

    def __str__(self):
        return f"{self.nombre} ({self.servicio.nombre})"