from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.contrib import messages
from empleados.views import es_admin
from django.core.exceptions import PermissionDenied
from empleados.models import Incidente, IncidenteEmpleado, Empleado, SancionEmpleado, Resolucion
from .forms import IncidenteForm
from sanciones.forms import ResolucionForm
from sanciones.forms import SancionMasivaForm
from django.utils import timezone

@login_required
@user_passes_test(es_admin)
def ver_incidentes(request):
    incidentes = Incidente.objects.all().order_by('-id')
    incidentes_list = []
    for incidente in incidentes:
        involucrados = IncidenteEmpleado.objects.filter(id_incidente=incidente).select_related('id_empl')
        if involucrados.exists():
            incidentes_list.append({
                'incidente': incidente,
                'involucrados': [ie.id_empl for ie in involucrados],
                'fecha_ocurrencia': involucrados.first().fecha_ocurrencia,
            })
    return render(request, 'ver_incidentes.html', {'incidentes_list': incidentes_list})

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
            return redirect('ver_incidentes')

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
            incidente = form.save(commit=False)
            
            empleados_seleccionados = form.cleaned_data['empleados_involucrados']
            
            IncidenteEmpleado.objects.filter(id_incidente=incidente).delete()
            
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
            
            incidente.save()
            messages.success(request, 'El incidente ha sido actualizado exitosamente.')
            return redirect('detalle_incidente', incidente_id=incidente.id)
    else:
        current_involved_employees = IncidenteEmpleado.objects.filter(id_incidente=incidente).values_list('id_empl', flat=True)
        
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
    messages.error(request, 'Método no permitido para eliminar directamente. Por favor, confirma la eliminación.')
    return redirect('detalle_incidente', incidente_id=incidente.id)

@login_required
@user_passes_test(es_admin)
def detalle_incidente(request, incidente_id):
    incidente = get_object_or_404(Incidente, id=incidente_id)
    
    involucrados_qs = IncidenteEmpleado.objects.filter(id_incidente=incidente).select_related('id_empl', 'id_descargo', 'id_resolucion')
    
    sanciones_existentes = SancionEmpleado.objects.filter(incidente_asociado__in=involucrados_qs).values_list('incidente_asociado_id', flat=True)

    involucrados = []
    descargos = []
    for inv in involucrados_qs:
        inv.ya_sancionado = inv.id in sanciones_existentes
        involucrados.append(inv)
        if inv.id_descargo:
            descargos.append({'empleado': inv.id_empl, 'descargo': inv.id_descargo})

    resolucion = None
    for inv in involucrados_qs:
        if inv.id_resolucion:
            resolucion = inv.id_resolucion
            break

    first_inc_empl = involucrados_qs.first()
    fecha_incidente = first_inc_empl.fecha_ocurrencia if first_inc_empl else None
    motivo_inicial = f"Derivado del incidente: '{incidente.tipo_incid}' ocurrido el {fecha_incidente.strftime('%d/%m/%Y') if fecha_incidente else 'N/A'}."
    sancion_form = SancionMasivaForm(initial={'motivo': motivo_inicial})
    
    resolucion_form = ResolucionForm()
    context = {
        'incidente': incidente,
        'involucrados': involucrados,
        'sancion_form': sancion_form,
        'fecha_incidente': fecha_incidente,
        'descargos': descargos,
        'resolucion': resolucion,
        'resolucion_form': resolucion_form,
    }
    return render(request, 'detalle_incidente.html', context)

@login_required
def ver_incidentes_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    es_propietario = hasattr(request.user, 'empleado') and request.user.empleado.id == empleado.id
    if not (es_admin(request.user) or es_propietario):
        raise PermissionDenied

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

@login_required
@user_passes_test(es_admin)
@transaction.atomic
def resolver_incidente(request, incidente_id):
    if request.method != 'POST':
        return redirect('detalle_incidente', incidente_id=incidente_id)

    incidente = get_object_or_404(Incidente, id=incidente_id)
    form = ResolucionForm(request.POST)

    if form.is_valid():
        resolucion = form.save(commit=False)
        resolucion.responsable = request.user.get_full_name() or request.user.username
        resolucion.fecha_resolucion = timezone.now().date()
        resolucion.save()

        IncidenteEmpleado.objects.filter(id_incidente=incidente).update(id_resolucion=resolucion)

        action = request.POST.get('action')
        if action == 'sancionar':
            return redirect('aplicar_sancion_masiva', incidente_id=incidente.id)
        else:
            messages.success(request, 'El incidente ha sido marcado como resuelto.')
            return redirect('detalle_incidente', incidente_id=incidente.id)
    
    messages.error(request, 'Hubo un error al procesar la resolución. Por favor, inténtalo de nuevo.')
    return redirect('detalle_incidente', incidente_id=incidente.id)