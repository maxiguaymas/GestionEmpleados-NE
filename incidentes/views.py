from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction, models
from django.contrib import messages
from empleados.views import es_admin
from django.core.exceptions import PermissionDenied
from empleados.models import Incidente, IncidenteEmpleado, Empleado, SancionEmpleado
from .forms import IncidenteForm
from sanciones.forms import SancionMasivaForm

@login_required
@user_passes_test(es_admin)
@transaction.atomic # Para asegurar la integridad de los datos
def registrar_incidente(request):
    if request.method == 'POST':
        form = IncidenteForm(request.POST)
        if form.is_valid():
            # Primero, guardamos el incidente principal
            incidente = form.save()

            # Obtenemos los datos adicionales del formulario
            empleados = form.cleaned_data['empleados_involucrados']
            observaciones = form.cleaned_data['observaciones']
            fecha_incidente = form.cleaned_data['fecha_incid']
            responsable = request.user.get_full_name() or request.user.username

            # Ahora, creamos un registro en IncidenteEmpleado para cada empleado
            for empleado in empleados:
                IncidenteEmpleado.objects.create(
                    id_incidente=incidente,
                    id_empl=empleado,
                    fecha_ocurrencia=fecha_incidente,
                    observaciones=observaciones,
                    responsable_registro=responsable,
                    estado=True # O el estado inicial que definas
                )
            
            messages.success(request, 'El incidente ha sido registrado exitosamente.')
            # Redirigir a una futura vista de lista de incidentes
            return redirect('ver_incidentes') # Asumimos que esta ruta existirá

    else:
        form = IncidenteForm()

    return render(request, 'registrar_incidente.html', {'form': form})

@login_required
@user_passes_test(es_admin)
@transaction.atomic
def editar_incidente(request, incidente_id):
    incidente = get_object_or_404(Incidente, id=incidente_id)
    if request.method == 'POST':
        form = IncidenteForm(request.POST, instance=incidente)
        if form.is_valid():
            incidente = form.save(commit=False) # Don't save yet, need to handle m2m
            
            # Handle empleados_involucrados (Many-to-Many relationship)
            empleados_seleccionados = form.cleaned_data['empleados_involucrados']
            
            # Clear existing IncidenteEmpleado entries for this incident
            IncidenteEmpleado.objects.filter(id_incidente=incidente).delete()
            
            # Recreate IncidenteEmpleado entries
            observaciones = form.cleaned_data['observaciones']
            responsable = request.user.get_full_name() or request.user.username
            for empleado in empleados_seleccionados:
                IncidenteEmpleado.objects.create(
                    id_incidente=incidente,
                    id_empl=empleado,
                    observaciones=observaciones,
                    responsable_registro=responsable,
                    estado=True
                )
            
            incidente.save() # Now save the incident itself
            messages.success(request, 'El incidente ha sido actualizado exitosamente.')
            return redirect('detalle_incidente', incidente_id=incidente.id)
    else:
        # For GET request, pre-populate the form
        # Get current involved employees for the form's initial data
        current_involved_employees = IncidenteEmpleado.objects.filter(id_incidente=incidente).values_list('id_empl', flat=True)
        
        # Get observations from one of the IncidenteEmpleado entries, if any
        # Assuming observations are consistent across all involved employees for this incident
        first_inc_empl = IncidenteEmpleado.objects.filter(id_incidente=incidente).first()
        initial_observaciones = first_inc_empl.observaciones if first_inc_empl else ''

        form = IncidenteForm(instance=incidente, initial={
            'empleados_involucrados': list(current_involved_employees),
            'observaciones': initial_observaciones
        })
    return render(request, 'editar_incidente.html', {'form': form, 'incidente': incidente})

@login_required
@user_passes_test(es_admin)
def eliminar_incidente(request, incidente_id):
    incidente = get_object_or_404(Incidente, id=incidente_id)
    if request.method == 'POST':
        incidente.delete()
        messages.success(request, 'El incidente ha sido eliminado exitosamente.')
        return redirect('ver_incidentes')
    # For GET request, render a confirmation page (or just redirect if no confirmation needed)
    # A proper implementation would render a confirmation template.
    messages.error(request, 'Método no permitido para eliminar directamente. Por favor, confirma la eliminación.')
    return redirect('detalle_incidente', incidente_id=incidente.id)

# También necesitarás una vista para listar los incidentes
@login_required
@user_passes_test(es_admin)
def ver_incidentes(request):
    incidentes_empleado = IncidenteEmpleado.objects.select_related('id_incidente', 'id_empl').all().order_by('-fecha_ocurrencia')
    return render(request, 'ver_incidentes.html', {'incidentes_empleado': incidentes_empleado})

@login_required
@user_passes_test(es_admin)
def detalle_incidente(request, incidente_id):
    incidente = get_object_or_404(Incidente, id=incidente_id)
    
    # Obtenemos los involucrados y verificamos si ya tienen una sanción para este incidente
    involucrados_qs = IncidenteEmpleado.objects.filter(id_incidente=incidente).select_related('id_empl')
    sanciones_existentes = SancionEmpleado.objects.filter(incidente_asociado__in=involucrados_qs).values_list('incidente_asociado_id', flat=True)

    involucrados = []
    for inv in involucrados_qs:
        inv.ya_sancionado = inv.id in sanciones_existentes
        involucrados.append(inv)

    # Pre-llenamos el motivo del formulario de sanción
    first_inc_empl = involucrados_qs.first()
    fecha_incidente = first_inc_empl.fecha_ocurrencia if first_inc_empl else None
    motivo_inicial = f"Derivado del incidente: '{incidente.tipo_incid}' ocurrido el {fecha_incidente.strftime('%d/%m/%Y') if fecha_incidente else 'N/A'}."
    sancion_form = SancionMasivaForm(initial={'motivo': motivo_inicial})
    
    return render(request, 'detalle_incidente.html', {
        'incidente': incidente,
        'involucrados': involucrados,
        'sancion_form': sancion_form,
        'fecha_incidente': fecha_incidente
    })

@login_required
def ver_incidentes_empleado(request, empleado_id):
    # Obtenemos el empleado o mostramos un error 404 si no existe
    empleado = get_object_or_404(Empleado, id=empleado_id)
    # Lógica de permisos:
    # Permitir si es admin O si el empleado está editando su propio perfil.
    es_propietario = hasattr(request.user, 'empleado') and request.user.empleado.id == empleado.id
    if not (es_admin(request.user) or es_propietario):
        raise PermissionDenied

    # Buscamos todas las entradas en IncidenteEmpleadoDescargo para este empleado.
    # Usamos select_related para optimizar la consulta y traer los datos del incidente relacionado
    # en una sola query a la base de datos.
    incidentes_empleado = IncidenteEmpleado.objects.filter(id_empl=empleado).select_related('id_incidente').order_by('-fecha_ocurrencia')

    context = {
        'empleado': empleado,
        'incidentes_empleado': incidentes_empleado
    }

    return render(request, 'ver_incidentes_empleado.html', context)

@login_required
def mis_incidentes(request):
    try:
        empleado = request.user.empleado
        incidentes = IncidenteEmpleado.objects.filter(id_empl=empleado).select_related('id_incidente').order_by('-fecha_ocurrencia')
    except Empleado.DoesNotExist:
        incidentes = IncidenteEmpleado.objects.none()
    
    context = {
        'incidentes_empleado': incidentes,
    }
    return render(request, 'mis_incidentes.html', context)