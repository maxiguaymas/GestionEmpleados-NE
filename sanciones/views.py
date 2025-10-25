from django.shortcuts import render, get_object_or_404, redirect
from empleados.views import es_admin
from empleados.models import Empleado, SancionEmpleado, IncidenteEmpleado, Incidente, Sancion, Resolucion, Notificacion
from .forms import SancionEmpleadoForm, SancionMasivaForm, ResolucionForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import get_template, render_to_string
from django.db.models import Q
from django.core.mail import send_mail
from xhtml2pdf import pisa
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required
def sanciones_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    # Lógica de permisos:
    # Permitir si es admin O si el empleado está editando su propio perfil.
    es_propietario = hasattr(request.user, 'empleado') and request.user.empleado.id == empleado.id
    if not (es_admin(request.user) or es_propietario):
        raise PermissionDenied
    sanciones_query = SancionEmpleado.objects.filter(id_empl=empleado).select_related('id_sancion').order_by('-fecha_inicio')

    # Get filter parameters
    month = request.GET.get('month')
    year = request.GET.get('year')
    tipo_sancion = request.GET.get('tipo')

    # Apply filters
    if month and year:
        try:
            sanciones_query = sanciones_query.filter(fecha_inicio__month=int(month), fecha_inicio__year=int(year))
        except (ValueError, TypeError):
            pass
    if tipo_sancion:
        sanciones_query = sanciones_query.filter(id_sancion__tipo__iexact=tipo_sancion)

    # Get distinct sanction types and years for filter dropdowns
    tipos_sancion = Sancion.objects.values_list('tipo', flat=True).distinct()
    years = sanciones_query.dates('fecha_inicio', 'year').reverse()

    # Paginación
    registros_por_pagina = request.GET.get('por_pagina', '9')
    paginator = Paginator(sanciones_query, registros_por_pagina)
    page_number = request.GET.get('page')
    sanciones_paginadas = paginator.get_page(page_number)

    context = {
        'empleado': empleado,
        'sanciones_paginadas': sanciones_paginadas,
        'page_title': 'Sanciones del Empleado',
        'filter_values': request.GET,
        'tipos_sancion': tipos_sancion,
        'year_options': [d.year for d in years],
        'por_pagina': registros_por_pagina,
    }
    return render(request, 'sanciones_empleado.html', context)

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

            # Crear notificación
            Notificacion.objects.create(
                id_user=empleado.user,
                mensaje=f"Se le ha registrado una nueva sanción: {sancion_empleado.id_sancion.nombre}",
                enlace=reverse('detalle_sancion', args=[sancion_empleado.id])
            )

            # Enviar correo electrónico de notificación
            try:
                print(f"Intentando enviar correo de sanción a: {empleado.email}")
                detalle_url = request.build_absolute_uri(reverse('detalle_sancion', args=[sancion_empleado.id]))
                asunto = f"Notificación de Nueva Sanción: {sancion_empleado.id_sancion.nombre}"

                # Mensaje en texto plano como alternativa
                cuerpo_mensaje_plain = (
                    f"Hola {empleado.nombre},\n\n"
                    f"Se te ha registrado una nueva sanción: {sancion_empleado.id_sancion.nombre}.\n"
                    f"Motivo: {sancion_empleado.motivo}\n"
                    f"Fecha de inicio: {sancion_empleado.fecha_inicio.strftime('%d/%m/%Y')}\n\n"
                    f"Puedes ver los detalles en el portal: {detalle_url}\n\n"
                    "Saludos,\nEl equipo de RRHH"
                )

                cuerpo_mensaje_html = render_to_string('email/notificacion_sancion.html', {
                    'empleado_nombre': empleado.nombre,
                    'sancion_empleado': sancion_empleado,
                    'detalle_url': detalle_url,
                })
                send_mail(asunto, cuerpo_mensaje_plain, None, [empleado.email], html_message=cuerpo_mensaje_html)
            except Exception as e:
                print(f"ERROR al enviar correo de sanción: {e}")

            messages.success(request, f"Sanción agregada exitosamente a {empleado.nombre} {empleado.apellido}.")
            return redirect('detalle_sancion', sancion_empleado.id)
    # Si se encontró un empleado (por GET), mostrar el formulario para llenarlo
    elif empleado:
        form = SancionEmpleadoForm()
    else:
        form = None

    return render(request, 'agregar_sancion.html', {
        'empleado': empleado,
        'form': form,
        'mensaje': mensaje,
        'page_title': 'Agregar Sanción',
    })

@login_required
@user_passes_test(es_admin)
@transaction.atomic
def aplicar_sancion_masiva(request, incidente_id):
    incidente = get_object_or_404(Incidente, id=incidente_id)
    involucrados_qs = IncidenteEmpleado.objects.filter(id_incidente=incidente).select_related('id_empl')
    
    # Exclude already sanctioned employees for this incident
    sancionados_ids = SancionEmpleado.objects.filter(incidente_asociado__in=involucrados_qs).values_list('incidente_asociado__id_empl_id', flat=True)
    involucrados_a_sancionar = involucrados_qs.exclude(id_empl_id__in=sancionados_ids)

    if not involucrados_a_sancionar:
        messages.info(request, "Todos los empleados de este incidente ya tienen una sanción asociada.")
        return redirect('detalle_incidente', incidente_id=incidente.id)

    if request.method == 'POST':
        forms = [SancionEmpleadoForm(request.POST, prefix=str(inv.id)) for inv in involucrados_a_sancionar]
        if all(form.is_valid() for form in forms):
            sanciones_creadas = False
            for i, form in enumerate(forms):
                # Only save if a sanction type was selected
                if form.cleaned_data.get('id_sancion'):
                    sancion = form.save(commit=False)
                    involucrado = involucrados_a_sancionar[i]
                    sancion.id_empl = involucrado.id_empl
                    sancion.incidente_asociado = involucrado
                    sancion.responsable = request.user.get_full_name() or request.user.username
                    sancion.save()

                    # Crear notificación
                    Notificacion.objects.create(
                        id_user=sancion.id_empl.user,
                        mensaje=f"Se le ha registrado una nueva sanción: {sancion.id_sancion.nombre}",
                        enlace=reverse('detalle_sancion', args=[sancion.id])
                    )

                    # Enviar correo electrónico de notificación
                    try:
                        print(f"Intentando enviar correo de sanción a: {sancion.id_empl.email}")
                        detalle_url = request.build_absolute_uri(reverse('detalle_sancion', args=[sancion.id]))
                        asunto = f"Notificación de Nueva Sanción: {sancion.id_sancion.nombre}"

                        cuerpo_mensaje_plain = (
                            f"Hola {sancion.id_empl.nombre},\n\n"
                            f"Se te ha registrado una nueva sanción: {sancion.id_sancion.nombre}.\n"
                            f"Motivo: {sancion.motivo}\n"
                            f"Fecha de inicio: {sancion.fecha_inicio.strftime('%d/%m/%Y')}\n\n"
                            f"Puedes ver los detalles en el portal: {detalle_url}\n\n"
                            "Saludos,\nEl equipo de RRHH"
                        )

                        cuerpo_mensaje_html = render_to_string('email/notificacion_sancion.html', {
                            'empleado_nombre': sancion.id_empl.nombre,
                            'sancion_empleado': sancion,
                            'detalle_url': detalle_url,
                        })
                        send_mail(asunto, cuerpo_mensaje_plain, None, [sancion.id_empl.email], html_message=cuerpo_mensaje_html)
                    except Exception as e:
                        print(f"ERROR al enviar correo de sanción masiva: {e}")

                    sanciones_creadas = True
            
            # If at least one sanction was created, create the resolution
            if sanciones_creadas:
                resolucion_descripcion = request.session.get('resolucion_descripcion')
                if resolucion_descripcion:
                    resolucion = Resolucion.objects.create(
                        descripcion=resolucion_descripcion,
                        responsable=request.user.get_full_name() or request.user.username,
                        fecha_resolucion=timezone.now().date()
                    )
                    involucrados_qs.update(id_resolucion=resolucion)
                    del request.session['resolucion_descripcion']

            messages.success(request, "Sanciones aplicadas correctamente.")
            return redirect('detalle_incidente', incidente_id=incidente.id)
    else:
        forms = [SancionEmpleadoForm(prefix=str(inv.id), initial={'motivo': f"Derivado del incidente: '{incidente.tipo_incid}'"}) for inv in involucrados_a_sancionar]

    involucrados_forms = zip(involucrados_a_sancionar, forms)

    context = {
        'incidente': incidente,
        'involucrados_forms': involucrados_forms,
        'page_title': 'Aplicar Sanción Masiva',
    }
    return render(request, 'aplicar_sancion_masiva.html', context)

@login_required
@user_passes_test(es_admin)
def ver_todas_sanciones(request):
    sanciones_query = SancionEmpleado.objects.select_related('id_empl', 'id_sancion').order_by('-fecha_inicio')

    # Get filter parameters
    search_query = request.GET.get('q')
    month = request.GET.get('month')
    year = request.GET.get('year')
    tipo_sancion = request.GET.get('tipo')

    # Apply filters
    if search_query:
        sanciones_query = sanciones_query.filter(
            Q(id_empl__nombre__icontains=search_query) |
            Q(id_empl__apellido__icontains=search_query) |
            Q(id_empl__dni__icontains=search_query)
        )

    try:
        if month:
            sanciones_query = sanciones_query.filter(fecha_inicio__month=int(month))
        if year:
            sanciones_query = sanciones_query.filter(fecha_inicio__year=int(year))
    except (ValueError, TypeError):
        pass

    if tipo_sancion:
        sanciones_query = sanciones_query.filter(id_sancion__tipo__iexact=tipo_sancion)

    # Get distinct sanction types for the filter dropdown
    tipos_sancion = Sancion.objects.values_list('tipo', flat=True).distinct()

    # Get the range of years present in the data
    years = SancionEmpleado.objects.dates('fecha_inicio', 'year').reverse()

    # Paginación
    registros_por_pagina = request.GET.get('por_pagina', 9)
    paginator = Paginator(sanciones_query, registros_por_pagina)
    page_number = request.GET.get('page')
    sanciones_paginadas = paginator.get_page(page_number)

    context = {
        'sanciones_paginadas': sanciones_paginadas,
        'titulo': 'Historial de Sanciones',
        'page_title': 'Sanciones',
        'filter_values': request.GET,
        'tipos_sancion': tipos_sancion,
        'year_options': [d.year for d in years],
        'por_pagina': registros_por_pagina,
    }
    return render(request, 'ver_todas_sanciones.html', context)

@login_required
@user_passes_test(es_admin)
@transaction.atomic
def agregar_resolucion(request, sancion_empleado_id): # pragma: no cover
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
        'sancion': sancion_empleado,
        'page_title': 'Agregar Resolución',
    })
    
    
def detalle_sancion(request, sancion_id):
    """
    Muestra los detalles de una sanción específica.
    """
    sancionEmpleado = get_object_or_404(SancionEmpleado, pk=sancion_id)
    sancion = sancionEmpleado.id_sancion
    
    context = {
        'sancion_empleado': sancionEmpleado,
        'sancion': sancion,
        'page_title': 'Detalle de Sanción',
    }
    return render(request, 'detalle_sancion.html', context)

@login_required
def mis_sanciones(request):
    try:
        empleado = request.user.empleado
        sanciones = SancionEmpleado.objects.filter(id_empl=empleado).order_by('-fecha_inicio')
        
        # Aplicar filtros si existen
        month = request.GET.get('month')
        year = request.GET.get('year')
        tipo = request.GET.get('tipo')

        if month:
            sanciones = sanciones.filter(fecha_inicio__month=int(month))
        if year:
            sanciones = sanciones.filter(fecha_inicio__year=int(year))
        if tipo:
            sanciones = sanciones.filter(id_sancion__tipo=tipo)

        # Configuración de la paginación
        por_pagina = request.GET.get('por_pagina', '9')
        paginator = Paginator(sanciones, por_pagina)
        page_number = request.GET.get('page')
        sanciones_paginadas = paginator.get_page(page_number)
        
        # Obtener años disponibles y tipos de sanción
        # Se usa el queryset original sin filtros para obtener todos los años posibles
        years_dates = SancionEmpleado.objects.filter(id_empl=empleado).dates('fecha_inicio', 'year', order='DESC')
        years = [d.year for d in years_dates]
        tipos_sancion = Sancion.objects.values_list('tipo', flat=True).distinct()

        context = {
            'sanciones_paginadas': sanciones_paginadas,
            'filter_values': {
                'month': month or '',
                'year': year or '',
                'tipo': tipo or '',
            },
            'tipos_sancion': tipos_sancion,
            'year_options': years,
            'por_pagina': por_pagina,
            'page_title': 'Mis Sanciones'
        }

        return render(request, 'mis_sanciones.html', context)
        
    except Empleado.DoesNotExist:
        context = {
            'error_message': 'No se encontró tu perfil de empleado.',
            'page_title': 'Mis Sanciones'
        }
        return render(request, 'mis_sanciones.html', context)

# Copia esta función de ayuda para generar PDFs
def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    response = HttpResponse(content_type='application/pdf')
    # Para descargar directamente, cambia 'inline' por 'attachment'
    response['Content-Disposition'] = f'inline; filename="sancion_{context_dict.get("sancion_id", "0")}.pdf"'

    pisa_status = pisa.CreatePDF(
        html, dest=response
    )
    if pisa_status.err:
        return HttpResponse('Tuvimos algunos errores <pre>' + html + '</pre>')
    return response

# Esta es la nueva vista para generar el PDF de la sanción
@login_required
def generar_sancion_pdf(request, sancion_id):
    sancion_empleado = get_object_or_404(SancionEmpleado.objects.select_related('id_empl', 'id_sancion'), id=sancion_id)

    context = {
        'sancion_empleado': sancion_empleado,
        'sancion_id': sancion_id,
    }

    return render_to_pdf('sancion_pdf.html', context)