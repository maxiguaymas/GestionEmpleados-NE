from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from empleados.models import Recibo_Sueldos as Recibo, Empleado
from .forms import ReciboSueldoForm
from empleados.views import es_admin
from django.contrib.auth.decorators import user_passes_test

@user_passes_test(es_admin)
def cargar_recibo(request):
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesiÃ³n para cargar un recibo.")
        return redirect('login')
    
    if request.method == 'POST':
        form = ReciboSueldoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
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
    except AttributeError:
        recibos = Recibo.objects.none()
        empleado = None
    return render(request, 'mis_recibos.html', {
        'recibos': recibos,
        'empleado_seleccionado': empleado,
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