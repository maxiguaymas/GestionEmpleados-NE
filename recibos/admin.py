from django.contrib import admin
from empleados.models import Recibo_Sueldos

class ReciboSueldosAdmin(admin.ModelAdmin):
    list_display = ('id_empl', 'periodo', 'fecha_emision')
    search_fields = ['id_empl__dni', 'id_empl__nombre', 'id_empl__apellido']
    list_filter = ('fecha_emision',)

admin.site.register(Recibo_Sueldos, ReciboSueldosAdmin)