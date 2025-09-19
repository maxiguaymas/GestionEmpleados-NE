from django import forms
from empleados.models import Incidente, Empleado, Resolucion

class IncidenteForm(forms.ModelForm):
    empleados_involucrados = forms.ModelMultipleChoiceField(
        queryset=Empleado.objects.filter(estado='Activo'),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Empleados Involucrados"
    )

    observaciones = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label="Observaciones Generales (para todos los involucrados)"
    )

    fecha_incid = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Fecha del Incidente"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tipos = [('', 'Seleccionar...')] + list(Incidente.objects.values_list('tipo_incid', 'tipo_incid').distinct())
        self.fields['tipo_incid'] = forms.ChoiceField(
            choices=tipos,
            label='Tipo de Incidente'
        )

    class Meta:
        model = Incidente
        fields = [
            'tipo_incid',
            'descripcion_incid',
        ]
        labels = {
            'descripcion_incid': 'Descripción',
        }
