from django import forms
from empleados.models import Horarios, AsignacionHorario, Empleado
from datetime import time

class HorarioForm(forms.ModelForm):
    class Meta:
        model = Horarios
        fields = [
            'nombre', 'hora_entrada', 'hora_salida', 
            'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo',
            'cantidad_personal_requerida'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 shadow-sm focus:border-red-500 focus:ring-red-500'}),
            'hora_entrada': forms.TimeInput(attrs={'type': 'time', 'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 shadow-sm focus:border-red-500 focus:ring-red-500'}),
            'hora_salida': forms.TimeInput(attrs={'type': 'time', 'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 shadow-sm focus:border-red-500 focus:ring-red-500'}),
            'cantidad_personal_requerida': forms.NumberInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 shadow-sm focus:border-red-500 focus:ring-red-500', 'min': '1'}),
            'lunes': forms.CheckboxInput(attrs={'class': 'h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500'}),
            'martes': forms.CheckboxInput(attrs={'class': 'h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500'}),
            'miercoles': forms.CheckboxInput(attrs={'class': 'h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500'}),
            'jueves': forms.CheckboxInput(attrs={'class': 'h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500'}),
            'viernes': forms.CheckboxInput(attrs={'class': 'h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500'}),
            'sabado': forms.CheckboxInput(attrs={'class': 'h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500'}),
            'domingo': forms.CheckboxInput(attrs={'class': 'h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500'}),
        }
        labels = {
            'nombre': 'Nombre del Horario',
            'hora_entrada': 'Hora de Entrada',
            'hora_salida': 'Hora de Salida',
            'cantidad_personal_requerida': 'Personal Requerido',
            'lunes': 'Lun', 'martes': 'Mar', 'miercoles': 'Mié', 'jueves': 'Jue', 'viernes': 'Vie', 'sabado': 'Sáb', 'domingo': 'Dom',
        }

class HorarioPresetForm(forms.Form):
    TURNO_CHOICES = [
        ('manana', 'Turno Mañana (09:00 - 13:00, L-V)'),
        ('tarde', 'Turno Tarde (14:00 - 18:00, L-V)'),
    ]
    turno = forms.ChoiceField(choices=TURNO_CHOICES, label="Turno Predefinido", widget=forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 shadow-sm focus:border-red-500 focus:ring-red-500'}))
    cantidad_personal_requerida = forms.IntegerField(label="Cantidad de Personal Requerido", min_value=1, widget=forms.NumberInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 shadow-sm focus:border-red-500 focus:ring-red-500', 'min': '1'}))

    def save(self):
        data = self.cleaned_data
        if data['turno'] == 'manana':
            horario, created = Horarios.objects.get_or_create(
                nombre="Turno Mañana",
                defaults={
                    'hora_entrada': time(9, 0),
                    'hora_salida': time(13, 0),
                    'lunes': True, 'martes': True, 'miercoles': True, 'jueves': True, 'viernes': True,
                    'sabado': False, 'domingo': False,
                    'cantidad_personal_requerida': data['cantidad_personal_requerida']
                }
            )
            if not created:
                pass
            return horario, created
        elif data['turno'] == 'tarde':
            horario, created = Horarios.objects.get_or_create(
                nombre="Turno Tarde",
                defaults={
                    'hora_entrada': time(14, 0),
                    'hora_salida': time(18, 0),
                    'lunes': True, 'martes': True, 'miercoles': True, 'jueves': True, 'viernes': True,
                    'sabado': False, 'domingo': False,
                    'cantidad_personal_requerida': data['cantidad_personal_requerida']
                }
            )
            if not created:
                pass
            return horario, created
        return None


class AsignarHorarioForm(forms.ModelForm):
    id_empl = forms.ModelChoiceField(
        queryset=Empleado.objects.filter(estado='Activo'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Empleado"
    )
    id_horario = forms.ModelChoiceField(
        queryset=Horarios.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Horario"
    )

    class Meta:
        model = AsignacionHorario
        fields = ['id_empl', 'id_horario', 'estado']
        widgets = {
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Opcional: filtrar empleados que ya tienen horario
        # empleados_con_horario = AsignacionHorario.objects.filter(estado=True).values_list('id_empl', flat=True)
        # self.fields['id_empl'].queryset = Empleado.objects.filter(estado='Activo').exclude(id__in=empleados_con_horario)