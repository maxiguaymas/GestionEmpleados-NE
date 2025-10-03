from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from empleados.models import Recibo_Sueldos as Recibo, Empleado, Notificacion
from .forms import ReciboSueldoForm
from empleados.views import es_admin
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse
import datetime

@user_passes_test(es_admin)
def cargar_recibo(request):
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesión para cargar un recibo.")
        return redirect('login')
    
    if request.method == 'POST':
        form = ReciboSueldoForm(request.POST, request.FILES)
        if form.is_valid():
            recibo = form.save()
            
            # Crear notificación
            empleado = recibo.id_empl
            mensaje = f"Se ha cargado tu recibo de sueldo para el período {recibo.periodo}."
            link = reverse('mis_recibos')
            Notificacion.objects.create(
                id_user=empleado.user,
                mensaje=mensaje,
                enlace=link
            )

            messages.success(request, "Recibo cargado correctamente.")
            return redirect('recibos_admin')
    else:
        form = ReciboSueldoForm()
    return render(request, 'recibos.html', {'form': form})

@user_passes_test(es_admin)
def recibos_admin(request):
    form = ReciboSueldoForm()
    return render(request, 'recibos.html', {'form': form})

def mis_recibos(request):
    try:
        empleado = request.user.empleado
        recibos = Recibo.objects.filter(id_empl=empleado).order_by('-fecha_emision')
        
        # Lógica de filtrado
        mes = request.GET.get('mes')
        anio = request.GET.get('anio')
        
        years = Recibo.objects.filter(id_empl=empleado).dates('fecha_emision', 'year').distinct()
        
        if mes and anio:
            recibos = recibos.filter(fecha_emision__month=mes, fecha_emision__year=anio)

    except AttributeError:
        recibos = Recibo.objects.none()
        empleado = None
        years = []

    return render(request, 'mis_recibos.html', {
        'recibos': recibos,
        'empleado_seleccionado': empleado,
        'years': years,
        'selected_month': int(mes) if mes else None,
        'selected_year': int(anio) if anio else None,
    })

def ver_recibos_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, pk=empleado_id)
    recibos = Recibo.objects.filter(id_empl=empleado).order_by('-fecha_emision')

    # Lógica de filtrado
    mes = request.GET.get('mes')
    anio = request.GET.get('anio')

    years = Recibo.objects.filter(id_empl=empleado).dates('fecha_emision', 'year').distinct()

    if mes and anio:
        recibos = recibos.filter(fecha_emision__month=mes, fecha_emision__year=anio)

    return render(request, 'ver_recibos_empleado.html', {
        'empleado': empleado,
        'recibos': recibos,
        'empleado_seleccionado': empleado,
        'years': years,
        'selected_month': int(mes) if mes else None,
        'selected_year': int(anio) if anio else None,
    })

def api_ver_recibos_empleado(request, dni):
    try:
        empleado = Empleado.objects.get(dni=dni)
        recibos = Recibo.objects.filter(id_empl=empleado).order_by('-fecha_emision')
        data = {
            'status': 'success',
            'empleado': {
                'nombre': empleado.nombre,
                'apellido': empleado.apellido,
            },
            'recibos': list(recibos.values('fecha_emision', 'periodo', 'ruta_pdf', 'ruta_imagen'))
        }
        return JsonResponse(data)
    except Empleado.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Empleado no encontrado.'}, status=404)

def ajax_buscar_empleado(request):
    q = request.GET.get('q', '')
    empleados = Empleado.objects.filter(dni__icontains=q)[:10]
    results = []
    for emp in empleados:
        results.append({
            'id': emp.id,
            'text': f"{emp.dni} - {emp.nombre} {emp.apellido}"
        })
    return JsonResponse({'results': results})
