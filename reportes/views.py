from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from empleados.models import Empleado
from django.db.models import Count

def reportes_home(request):
    return render(request, 'reportes/reportes_home.html')

def reporte_estado_empleados(request):
    # Agrupar por estado y contar empleados
    conteo_estados = Empleado.objects.values('estado').annotate(total=Count('estado')).order_by('estado')

    # Crear un diccionario para pasar al template
    context = {
        'conteo_estados': conteo_estados
    }
    return render(request, 'reportes/reporte_estado_empleados.html', context)