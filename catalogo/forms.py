from django import forms
from .models import Servicio, Componente, Contacto


class ServicioForm(forms.ModelForm):
    class Meta:
        model  = Servicio
        fields = ['slug', 'nombre']
        widgets = {
            'slug':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: recargas_paquetes'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: Recargas de paquetes'}),
        }
        help_texts = {
            'slug': 'Identificador único sin espacios ni caracteres especiales.',
        }


class ComponenteForm(forms.ModelForm):
    terminos_log = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Separados por coma: ERROR_CODE, FAIL_...'
        }),
        help_text='Términos opcionales separados por coma.'
    )

    class Meta:
        model  = Componente
        fields = ['id_componente', 'nombre', 'namespace', 'app_label', 'terminos_log']
        widgets = {
            'id_componente': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre':        forms.TextInput(attrs={'class': 'form-control'}),
            'namespace':     forms.TextInput(attrs={'class': 'form-control'}),
            'app_label':     forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_terminos_log(self):
        val = self.cleaned_data.get('terminos_log', '')
        if not val:
            return []
        return [t.strip() for t in val.split(',') if t.strip()]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.terminos_log:
            self.fields['terminos_log'].initial = ', '.join(self.instance.terminos_log)


class ContactoForm(forms.ModelForm):
    emails = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                     'placeholder': 'Un correo por línea'}),
        help_text='Un correo por línea.'
    )
    emails_copia = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                     'placeholder': 'Un correo por línea (opcional)'}),
        help_text='Un correo por línea.'
    )

    class Meta:
        model  = Contacto
        fields = ['nombre', 'emails', 'emails_copia', 'tipo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo':   forms.Select(attrs={'class': 'form-select'},
                                   choices=[('proveedor','Proveedor'),('interno','Interno')]),
        }

    def clean_emails(self):
        val = self.cleaned_data.get('emails', '')
        return [e.strip() for e in val.splitlines() if e.strip()]

    def clean_emails_copia(self):
        val = self.cleaned_data.get('emails_copia', '')
        return [e.strip() for e in val.splitlines() if e.strip()]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            if self.instance.emails:
                self.fields['emails'].initial = '\n'.join(self.instance.emails)
            if self.instance.emails_copia:
                self.fields['emails_copia'].initial = '\n'.join(self.instance.emails_copia)