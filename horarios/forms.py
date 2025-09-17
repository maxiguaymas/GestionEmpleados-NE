from django import forms
from empleados.models import Horarios, AsignacionHorario

class HorarioForm(forms.ModelForm):
    class Meta:
        model = Horarios
        fields = ['turno', 'dia', 'hora_entrada', 'hora_salida', 'cantidad_personal']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ == 'Select':
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
        
class AsignarHorarioForm(forms.ModelForm):
    class Meta:
        model = AsignacionHorario
        fields = ['id_empl', 'id_horario', 'estado']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'