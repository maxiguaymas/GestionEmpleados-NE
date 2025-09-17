from django import forms
from empleados.models import Empleado,Recibo_Sueldos

class ReciboSueldoForm(forms.ModelForm):
    id_empl = forms.ModelChoiceField(
        queryset=Empleado.objects.all(),
        label="Empleado",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Recibo_Sueldos
        fields = ['id_empl', 'fecha_emision', 'periodo', 'ruta_pdf', 'ruta_imagen']
        widgets = {
            'fecha_emision': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'periodo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'YYYY-MM'}),
            'ruta_pdf': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'ruta_imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }