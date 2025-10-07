from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.contrib import messages
from empleados.views import es_admin
from django.core.exceptions import PermissionDenied
from empleados.models import Incidente, IncidenteEmpleado, Empleado, SancionEmpleado, Resolucion, Notificacion
from django.urls import reverse
from .forms import IncidenteForm
from sanciones.forms import ResolucionForm
from sanciones.forms import SancionMasivaForm
from django.utils import timezone
import re
from django.db.models import Q

@login_required
@user_passes_test(es_admin)
def ver_incidentes(request):
    incidentes_query = Incidente.objects.all().order_by('-id')

    # Get filter parameters
    search_query = request.GET.get('q')
    month = request.GET.get('month')
    year = request.GET.get('year')
    status = request.GET.get('status')

    # Apply filters
    if search_query:
        incidentes_query = incidentes_query.filter(
            Q(incidenteempleado__id_empl__nombre__icontains=search_query) |
            Q(incidenteempleado__id_empl__apellido__icontains=search_query) |
            Q(incidenteempleado__id_empl__dni__icontains=search_query)
        )

    if month and year:
        try:
            incidentes_query = incidentes_query.filter(
                incidenteempleado__fecha_ocurrencia__month=int(month),
                incidenteempleado__fecha_ocurrencia__year=int(year)
            )
        except (ValueError, TypeError):
            pass # Or add a message

    if status:
        incidentes_query = incidentes_query.filter(incidenteempleado__estado__iexact=status)
    
    # Get unique incidents
    incidentes = incidentes_query.distinct()

    # Build the list for the template
    incidentes_list = []
    for incidente in incidentes:
        involucrados = IncidenteEmpleado.objects.filter(id_incidente=incidente).select_related('id_empl')
        if involucrados.exists():
            incidentes_list.append({
                'incidente': incidente,
                'involucrados': [ie.id_empl for ie in involucrados],
                'fecha_ocurrencia': involucrados.first().fecha_ocurrencia,
                'estado': involucrados.first().estado,
            })
    
    # For the year dropdown, find the range of years present in the data
    years = IncidenteEmpleado.objects.dates('fecha_ocurrencia', 'year').reverse()

    context = {
        'incidentes_list': incidentes_list,
        'filter_values': request.GET,
        'year_options': [d.year for d in years]
    }
    return render(request, 'ver_incidentes.html', context)

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
                    estado='ABIERTO' # Corregido
                )
                
                # Create notification
                mensaje = f"Has sido involucrado en un nuevo incidente: {incidente.tipo_incid}."
                link = reverse('detalle_incidente', args=[incidente.id])
                Notificacion.objects.create(
                    id_user=empleado.user,
                    mensaje=mensaje,
                    enlace=link
                )
            
            messages.success(request, 'El incidente ha sido registrado exitosamente.')
            return redirect('ver_incidentes')

    else:
        form = IncidenteForm()

    return render(request, 'registrar_incidente.html', {'form': form, 'page_title': 'Registrar Incidente'})


@login_required
@user_passes_test(es_admin)
@transaction.atomic
def corregir_incidente(request, incidente_id):
    incidente_original = get_object_or_404(Incidente, id=incidente_id)
    
    if request.method == 'POST':
        form = IncidenteForm(request.POST)
        if form.is_valid():
            # Crear un nuevo incidente
            nuevo_incidente = Incidente.objects.create(
                tipo_incid=incidente_original.tipo_incid,
                descripcion_incid=f"(Corrección del incidente #{incidente_original.id}) {incidente_original.descripcion_incid}"
            )

            # Obtener datos del formulario
            empleados_seleccionados = form.cleaned_data['empleados_involucrados']
            observaciones = form.cleaned_data['observaciones']
            fecha_incidente = form.cleaned_data['fecha_incid']
            responsable = request.user.get_full_name() or request.user.username

            # Crear nuevos registros de IncidenteEmpleado
            for empleado in empleados_seleccionados:
                IncidenteEmpleado.objects.create(
                    id_incidente=nuevo_incidente,
                    id_empl=empleado,
                    fecha_ocurrencia=fecha_incidente,
                    observaciones=observaciones,
                    responsable_registro=responsable,
                    estado='ABIERTO'
                )

            # Crear una resolución para el incidente original
            resolucion_cierre = Resolucion.objects.create(
                descripcion=f"Incidente cerrado automáticamente por corrección. Ver incidente #{nuevo_incidente.id}.",
                fecha_resolucion=timezone.now().date(),
                responsable=request.user.get_full_name() or request.user.username
            )

            # Cerrar los registros del incidente original y asociar la resolución
            IncidenteEmpleado.objects.filter(id_incidente=incidente_original).update(
                estado='CERRADO',
                id_resolucion=resolucion_cierre
            )

            messages.success(request, 'El incidente ha sido corregido exitosamente. Se ha creado un nuevo incidente y el original ha sido cerrado.')
            return redirect('detalle_incidente', incidente_id=nuevo_incidente.id)
    else:
        # Pre-rellenar el formulario con los datos del incidente original
        involucrados_originales = IncidenteEmpleado.objects.filter(id_incidente=incidente_original)
        empleados_originales = [ie.id_empl.id for ie in involucrados_originales]
        
        initial_data = {
            'tipo_incid': incidente_original.tipo_incid,
            'empleados_involucrados': empleados_originales,
            'observaciones': involucrados_originales.first().observaciones if involucrados_originales.exists() else '',
            'fecha_incid': involucrados_originales.first().fecha_ocurrencia if involucrados_originales.exists() else timezone.now().date(),
        }
        form = IncidenteForm(initial=initial_data)

    return render(request, 'corregir_incidente.html', {
        'form': form,
        'incidente': incidente_original,
        'page_title': 'Corregir Incidente',
    })





@login_required
@user_passes_test(es_admin)
def detalle_incidente(request, incidente_id):
    incidente = get_object_or_404(Incidente, id=incidente_id)
    
    corrected_incident_id = None
    if incidente.descripcion_incid:
        match = re.search(r'\(Corrección del incidente #(\d+)\)', incidente.descripcion_incid)
        if match:
            corrected_incident_id = int(match.group(1))

    involucrados_qs = IncidenteEmpleado.objects.filter(id_incidente=incidente).select_related('id_empl', 'id_descargo', 'id_resolucion', 'incidente_anterior', 'incidente_siguiente')
    
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
        'corrected_incident_id': corrected_incident_id,
        'page_title': 'Detalle de Incidente',
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
        'incidentes_empleado': incidentes_empleado,
        'page_title': 'Incidentes del Empleado',
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
        'page_title': 'Mis Incidentes',
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
        action = request.POST.get('action')
        if action == 'sancionar':
            # Store resolution description in session and redirect to apply sanctions
            request.session['resolucion_descripcion'] = form.cleaned_data['descripcion']
            return redirect('aplicar_sancion_masiva', incidente_id=incidente.id)
        else:
            # Just close the incident
            resolucion = form.save(commit=False)
            resolucion.responsable = request.user.get_full_name() or request.user.username
            resolucion.fecha_resolucion = timezone.now().date()
            resolucion.save()

            IncidenteEmpleado.objects.filter(id_incidente=incidente).update(id_resolucion=resolucion)
            messages.success(request, 'El incidente ha sido marcado como resuelto.')
            return redirect('detalle_incidente', incidente_id=incidente.id)
    
    messages.error(request, 'Hubo un error al procesar la resolución. Por favor, inténtalo de nuevo.')
    return redirect('detalle_incidente', incidente_id=incidente.id)

