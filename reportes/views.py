from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views import View
from empleados.models import Empleado, Sancion, Incidente
from django.db.models import Count

def reportes_home(request):
    # Esta vista ahora solo renderiza la página principal del dashboard.
    # El gráfico inicial se cargará vía fetch para ser consistente con los demás.
    return render(request, 'reportes/reportes_home.html')

def reporte_estado_empleados(request):
    conteo_estados = Empleado.objects.values('estado').annotate(total=Count('estado')).order_by('estado')
    context = {
        'conteo_estados': conteo_estados
    }
    return render(request, 'reportes/reporte_estado_empleados.html', context)

def reportes_sanciones_por_tipo(request):
    conteo_sanciones = Sancion.objects.values('tipo').annotate(total=Count('sancionempleado')).order_by('tipo')
    context = {
        'conteo_sanciones': conteo_sanciones
    }
    return render(request, 'reportes/reporte_sanciones_por_tipo.html', context)

def reporte_incidentes_por_tipo(request):
    conteo_incidentes = Incidente.objects.values('tipo_incid').annotate(total=Count('incidenteempleado')).order_by('tipo_incid')
    context = {
        'conteo_incidentes': conteo_incidentes
    }
    return render(request, 'reportes/reporte_incidentes_por_tipo.html', context)

# --- Endpoints de Datos para Gráficos Dinámicos ---

def reporte_estado_empleados_data(request):
    conteo = Empleado.objects.values('estado').annotate(total=Count('estado')).order_by('estado')
    labels = [item['estado'] for item in conteo]
    data = [item['total'] for item in conteo]
    return JsonResponse({'labels': labels, 'data': data})

def reporte_sanciones_data(request):
    conteo = Sancion.objects.values('tipo').annotate(total=Count('sancionempleado')).order_by('tipo')
    labels = [item['tipo'] for item in conteo]
    data = [item['total'] for item in conteo]
    return JsonResponse({'labels': labels, 'data': data})

def reporte_incidentes_data(request):
    conteo = Incidente.objects.values('tipo_incid').annotate(total=Count('incidenteempleado')).order_by('tipo_incid')
    labels = [item['tipo_incid'] for item in conteo]
    data = [item['total'] for item in conteo]
    return JsonResponse({'labels': labels, 'data': data})