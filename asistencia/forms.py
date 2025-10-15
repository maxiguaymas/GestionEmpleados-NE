from django import forms
import datetime

class AsistenciaFilterForm(forms.Form):
    MONTHS = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]
    
    current_year = datetime.datetime.now().year
    YEARS = [(year, year) for year in range(current_year - 5, current_year + 1)]

    month = forms.ChoiceField(
        choices=[('', 'Mes')] + MONTHS, 
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full pl-4 pr-4 py-2 rounded-lg border dark:bg-gray-700 dark:border-gray-600'
        })
    )
    year = forms.ChoiceField(
        choices=[('', 'Año')] + list(reversed(YEARS)), 
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full pl-4 pr-4 py-2 rounded-lg border dark:bg-gray-700 dark:border-gray-600'
        })
    )