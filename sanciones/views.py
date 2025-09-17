from django.shortcuts import render, get_object_or_404, redirect
from empleados.views import es_admin
from empleados.models import Empleado, SancionEmpleado, IncidenteEmpleado, Incidente, Sancion, Resolucion
from .forms import SancionEmpleadoForm, SancionMasivaForm, ResolucionForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.urls import reverse

@login_required
def sanciones_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    # Lógica de permisos:
    # Permitir si es admin O si el empleado está editando su propio perfil.
    es_propietario = hasattr(request.user, 'empleado') and request.user.empleado.id == empleado.id
    if not (es_admin(request.user) or es_propietario):
        raise PermissionDenied
    sanciones = SancionEmpleado.objects.filter(id_empl=empleado).select_related('id_sancion').prefetch_related('resoluciones')
    return render(request, 'ver_sanciones.html', {
        'empleado': empleado,
        'sanciones': sanciones,
    })

@login_required
@user_passes_test(es_admin)
def agregar_sancion_empleado(request):
    empleado = None
    mensaje = None

    # Si viene el DNI por GET, buscar el empleado
    dni = request.GET.get('dni')
    if dni:
        try:
            empleado = Empleado.objects.get(dni=dni)
        except Empleado.DoesNotExist:
            mensaje = "No se encontró un empleado con ese DNI."

    # Si ya se seleccionó el empleado, procesar el formulario de sanción
    if empleado and request.method == 'POST':
        form = SancionEmpleadoForm(request.POST)
        if form.is_valid():
            sancion_empleado = form.save(commit=False)
            # Asignar los campos que no vienen en el formulario
            sancion_empleado.id_empl = empleado
            sancion_empleado.responsable = request.user.get_full_name() or request.user.username
            sancion_empleado.save()
            messages.success(request, f"Sanción agregada exitosamente a {empleado.nombre} {empleado.apellido}.")
            return redirect('sanciones_empleado', empleado_id=empleado.id)
    # Si se encontró un empleado (por GET), mostrar el formulario para llenarlo
    elif empleado:
        form = SancionEmpleadoForm()
    else:
        form = None

    return render(request, 'agregar_sancion.html', {
        'empleado': empleado,
        'form': form,
        'mensaje': mensaje,
    })

@login_required
@user_passes_test(es_admin)
@transaction.atomic
def aplicar_sancion_masiva(request, incidente_id):
    incidente = get_object_or_404(Incidente, id=incidente_id)
    if request.method == 'POST':
        form = SancionMasivaForm(request.POST)
        # Obtenemos la lista de IDs de los registros IncidenteEmpleadoDescargo seleccionados
        involucrados_ids = request.POST.getlist('involucrados_a_sancionar')

        if not involucrados_ids:
            messages.error(request, 'Debe seleccionar al menos un empleado para aplicar la sanción.')
            return redirect('detalle_incidente', incidente_id=incidente.id)

        if form.is_valid():
            datos_sancion = form.cleaned_data
            responsable = request.user.get_full_name() or request.user.username
            
            involucrados = IncidenteEmpleado.objects.filter(id__in=involucrados_ids)

            for involucrado in involucrados:
                SancionEmpleado.objects.create(
                    id_empl=involucrado.id_empl,
                    id_sancion=datos_sancion['id_sancion'],
                    incidente_asociado=involucrado,
                    fecha_inicio=datos_sancion['fecha_inicio'],
                    fecha_fin=datos_sancion['fecha_fin'],
                    motivo=datos_sancion['motivo'],
                    responsable=responsable,
                )
            
            messages.success(request, f'Se aplicó la sanción a {len(involucrados_ids)} empleado(s) exitosamente.')
            return redirect('detalle_incidente', incidente_id=incidente.id)
        else:
            # Si el formulario no es válido, volvemos a renderizar la página de detalle
            # con el formulario y sus errores.
            messages.error(request, 'Por favor, corrija los errores en el formulario de sanción.')
            # Re-obtenemos los datos para la plantilla
            involucrados = IncidenteEmpleado.objects.filter(id_incidente=incidente).select_related('id_empl')
            return render(request, 'detalle_incidente.html', {
                'incidente': incidente,
                'involucrados': involucrados,
                'sancion_form': form # Pasamos el formulario con errores
            })

    # Si el método no es POST, simplemente redirigimos
    return redirect('detalle_incidente', incidente_id=incidente.id)

@login_required
@user_passes_test(es_admin)
def ver_todas_sanciones(request):
    # Usamos select_related para optimizar la consulta y evitar N+1 queries
    # al acceder a los datos del empleado y del tipo de sanción en la plantilla.
    sanciones = SancionEmpleado.objects.select_related('id_empl', 'id_sancion').order_by('-fecha_inicio')
    return render(request, 'ver_todas_sanciones.html', {
        'sanciones': sanciones,
        'titulo': 'Historial de Sanciones'
    })

@login_required
@user_passes_test(es_admin)
@transaction.atomic
def agregar_resolucion(request, sancion_empleado_id):
    sancion_empleado = get_object_or_404(SancionEmpleado, id=sancion_empleado_id)

    if request.method == 'POST':
        form = ResolucionForm(request.POST)
        if form.is_valid():
            resolucion = form.save(commit=False)
            resolucion.sancion_empleado = sancion_empleado
            resolucion.responsable = request.user.get_full_name() or request.user.username
            resolucion.estado = True
            resolucion.save()

            messages.success(request, 'La resolución ha sido agregada exitosamente.')
            return redirect('sanciones_empleado', empleado_id=sancion_empleado.id_empl.id)
    else:
        form = ResolucionForm()

    return render(request, 'agregar_resolucion.html', {
        'form': form,
        'sancion': sancion_empleado
    })
    
    
def detalle_sancion(request, sancion_id):
    """
    Muestra los detalles de una sanción específica.
    """
    sancionEmpleado = get_object_or_404(SancionEmpleado, pk=sancion_id)
    sancion = sancionEmpleado.id_sancion
    
    context = {
        'sancion_empleado': sancionEmpleado,
        'sancion': sancion
    }
    return render(request, 'detalle_sancion.html', context)

@login_required
def mis_sanciones(request):
    try:
        empleado = request.user.empleado
        sanciones = SancionEmpleado.objects.filter(id_empl=empleado).select_related('id_sancion').order_by('-fecha_inicio')
    except Empleado.DoesNotExist:
        sanciones = SancionEmpleado.objects.none()
    
    context = {
        'sanciones': sanciones,
    }
    return render(request, 'mis_sanciones.html', context)