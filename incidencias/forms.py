from django import forms
from catalogo.utils import get_servicios_choices

class IncidenciaForm(forms.Form):
    servicio = forms.ChoiceField(
        label='Servicio afectado',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    hora_inicio_novedad = forms.DateTimeField(
        label='Hora de inicio de la novedad',
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'},
            format='%Y-%m-%dT%H:%M',
        ),
        input_formats=['%Y-%m-%dT%H:%M'],
    )
    termino_error = forms.CharField(
        label='Término o código de error (opcional)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: ReadTimeoutException, 503, FAIL_INVALIDTRAZABILITYCODE...',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['servicio'].choices = [('', '-- Selecciona --')] + get_servicios_choices()


class PreviewForm(forms.Form):
    escalamiento_id = forms.IntegerField(widget=forms.HiddenInput)
    asunto = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    cuerpo = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 14}))
    destinatarios = forms.CharField(
        label='Destinatarios (uno por línea)',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
    )