from django import forms
from empleados.models import Incidente, Empleado

class IncidenteForm(forms.ModelForm):
    # Este campo nos permitirá seleccionar múltiples empleados.
    # No está en el modelo Incidente, lo manejaremos en la vista.
    empleados_involucrados = forms.ModelMultipleChoiceField(
        queryset=Empleado.objects.filter(estado='Activo'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500'}),
        required=True,
        label="Empleados Involucrados"
    )

    # Campo para las observaciones que se guardarán en IncidenteEmpleadoDescargo
    observaciones = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 shadow-sm', 'rows': 3}),
        required=False,
        label="Observaciones Generales (para todos los involucrados)"
    )

    fecha_incid = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 shadow-sm', 'type': 'date'}),
        label="Fecha del Incidente"
    )

    class Meta:
        model = Incidente
        fields = [
            'tipo_incid',
            'descripcion_incid',
        ]
        widgets = {
            'tipo_incid': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 shadow-sm'}),
            'descripcion_incid': forms.Textarea(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 shadow-sm', 'rows': 3}),
        }
        labels = {
            'tipo_incid': 'Tipo de Incidente',
            'descripcion_incid': 'Descripción',
        }