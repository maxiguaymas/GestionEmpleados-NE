from django import forms
from empleados.models import Incidente, Empleado, Resolucion, IncidenteEmpleado, Descargo
from django.utils import timezone

class IncidenteEmpleadoFilterForm(forms.Form):
    MONTH_CHOICES = [
        ('', 'Mes'),
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]
    
    current_year = timezone.now().year
    YEAR_CHOICES = [('', 'Año')] + [(year, year) for year in range(current_year - 10, current_year + 1)]

    STATUS_CHOICES = [
        ('', 'Estado'),
        ('ABIERTO', 'Abierto'),
        ('CERRADO', 'Cerrado'),
    ]

    common_attrs = {
        'class': 'w-full bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-red-500 focus:border-red-500 block p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-red-500 dark:focus:border-red-500'
    }

    month = forms.ChoiceField(choices=MONTH_CHOICES, required=False, label="", widget=forms.Select(attrs=common_attrs))
    year = forms.ChoiceField(choices=YEAR_CHOICES, required=False, label="", widget=forms.Select(attrs=common_attrs))
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False, label="", widget=forms.Select(attrs=common_attrs))

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

class DescargoForm(forms.ModelForm):
    class Meta:
        model = Descargo
        fields = ['contenido_descargo', 'ruta_archivo_descargo']
        widgets = {
            'contenido_descargo': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'contenido_descargo': 'Contenido del Descargo',
            'ruta_archivo_descargo': 'Adjuntar Archivo (Opcional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ruta_archivo_descargo'].required = False
        self.fields['ruta_archivo_descargo'].widget.attrs.update({'class': 'text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-red-50 file:text-red-700 hover:file:bg-red-100 dark:file:bg-red-900/50 dark:file:text-red-300 dark:hover:file:bg-red-900'})

