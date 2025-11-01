from django import forms
from .models import Empleado
from django.contrib.auth.models import Group

class EmpleadoForm(forms.ModelForm):
    grupo = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=True,
        label="Grupo",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    class Meta:
        model = Empleado
        exclude = ['user']
        fields = '__all__'
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'ruta_foto': forms.ClearableFileInput(attrs={'class': 'form-control'})
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si estamos editando, selecciona el grupo actual del usuario
        if self.instance and self.instance.pk and self.instance.user:
            grupos = self.instance.user.groups.all()
            if grupos.exists():
                self.fields['grupo'].initial = grupos.first()
        if self.instance and self.instance.pk:
            # Si es edición, deshabilita fecha_egreso
            self.fields['fecha_egreso'].widget.attrs['disabled'] = True
        else:
            # Si es creación, oculta fecha_egreso
            self.fields['fecha_egreso'].widget = forms.HiddenInput()
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.label_suffix = ''  # Opcional: quita los dos puntos automáticos
            field.widget.attrs['placeholder'] = field.label  # Opcional: placeholder igual al label
            # Agrega la clase al label
            field.widget.attrs['label_class'] = 'form-label'

        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'  # Bootstrap 5 recomienda 'form-select' para select
            else:
                field.widget.attrs['class'] = 'form-control'

    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        # self.instance es el objeto que se está editando.
        # Si estamos en modo de edición (self.instance.pk existe),
        # excluimos al propio empleado de la búsqueda de DNI duplicados.
        if self.instance and self.instance.pk:
            if Empleado.objects.filter(dni=dni).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Este DNI ya está registrado para otro empleado.")
        # Si estamos en modo de creación (no hay self.instance.pk),
        # simplemente comprobamos si el DNI ya existe.
        elif Empleado.objects.filter(dni=dni).exists():
            raise forms.ValidationError("Este DNI ya está registrado.")
        return dni
