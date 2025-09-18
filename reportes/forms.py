from django import forms

class ReporteAsistenciaForm(forms.Form):
    CHOICES = [
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
        ('anual', 'Anual')
    ]
    tipo_reporte = forms.ChoiceField(choices=CHOICES, required=True, label="Tipo de Reporte")
