from django.shortcuts import render
from asistencia.models import Asistencia
from .models import SancionEmpleado
from datetime import date, timedelta
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .forms import EmpleadoForm
from .models import Empleado, Notificacion, IncidenteEmpleado
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from empleados.models import Legajo, Documento, RequisitoDocumento
import pandas as pd
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.conf import settings
import json
from django.template.loader import render_to_string
from django.core.mail import send_mail
import os
import calendar
from django.utils.translation import gettext as _

def es_admin(user):
    return user.groups.filter(name='Administrador').exists() or user.is_superuser
# Create your views here.
def index(request):
    return render(request, 'index.html')

@login_required
@user_passes_test(es_admin)
def crear_empleado(request):
    form = EmpleadoForm()
    requisitos = RequisitoDocumento.objects.all()
    error = None

    if request.method == 'POST':
        form = EmpleadoForm(request.POST, request.FILES)
        archivos = request.FILES
        # 1. Validar documentos obligatorios
        for req in requisitos:
            if req.obligatorio and not archivos.get(f'doc_{req.id}'):
                error = f"El documento '{req.nombre_doc}' es obligatorio."
                break

        if not error and form.is_valid():
            # 2. Crear usuario, empleado, legajo y documentos
            empleado = form.save(commit=False)
            dni = form.cleaned_data['dni']
            grupo = form.cleaned_data['grupo']
            email = form.cleaned_data['email'] # Obtenemos el email del formulario

            # Creamos el usuario y le asignamos el email
            user = User.objects.create_user(username=str(dni), password=str(dni), email=email)
            user.groups.add(grupo)
            user.save()
            empleado.user = user
            empleado.save()

            # Crear notificación de bienvenida para el nuevo empleado
            Notificacion.objects.create(
                id_user=user,
                mensaje=f"¡Bienvenido/a, {empleado.nombre}! Tu perfil ha sido creado exitosamente.",
                enlace=reverse('ver_perfil')
            )

            # Enviar correo de bienvenida
            try:
                print(f"Intentando enviar correo de bienvenida a: {empleado.email}")
                login_url = request.build_absolute_uri(reverse('login'))
                asunto = "¡Bienvenido/a a Nuevas Energías! - Tu cuenta ha sido creada"
                
                # Mensaje en texto plano como alternativa
                cuerpo_mensaje_plain = (
                    f"Hola {empleado.nombre},\n\n"
                    f"¡Te damos la bienvenida a Nuevas Energías! Hemos creado tu cuenta en nuestro portal de empleados.\n\n"
                    f"Tus datos de acceso son:\n"
                    f"- Usuario: {dni}\n"
                    f"- Contraseña temporal: {dni}\n\n"
                    f"Puedes acceder al portal aquí: {login_url}\n\n"
                    "Por tu seguridad, te recomendamos cambiar tu contraseña después de iniciar sesión por primera vez.\n\n"
                    "Saludos,\nEl equipo de Administración"
                )

                # Renderizar el template HTML
                cuerpo_mensaje_html = render_to_string('email/bienvenida_empleado.html', {
                    'empleado_nombre': empleado.nombre,
                    'username': dni,
                    'password': dni, # La contraseña es el DNI
                    'login_url': login_url,
                })
                send_mail(asunto, cuerpo_mensaje_plain, settings.DEFAULT_FROM_EMAIL, [empleado.email], html_message=cuerpo_mensaje_html)
                print(f"Correo de bienvenida enviado exitosamente a {empleado.email}")
            except Exception as e:
                print(f"ERROR al enviar correo de bienvenida: {e}")

            nro_leg = Legajo.objects.count() + 1
            legajo = Legajo.objects.create(
                id_empl=empleado,
                estado_leg='Activo',
                nro_leg=nro_leg
            )

            for req in requisitos:
                archivo = archivos.get(f'doc_{req.id}')
                Documento.objects.create(
                    id_leg=legajo,
                    id_requisito=req,
                    ruta_archivo=archivo if archivo else None,
                    estado_doc=bool(archivo)
                )
            return redirect('empleados')
        else:
            return render(request, 'crear_empleado.html', {'form': form, 'error': error or 'Por favor corrige los errores.', 'requisitos': requisitos})

    return render(request, 'crear_empleado.html', {'form': form, 'requisitos': requisitos, 'page_title': 'Crear Empleado'})


@login_required
@user_passes_test(es_admin)
def editar_empleado(request, id):
    empleado = get_object_or_404(Empleado, id=id)
    legajo = getattr(empleado, 'legajo', None)
    documentos = Documento.objects.filter(id_leg=legajo) if legajo else []
    requisitos = RequisitoDocumento.objects.all()
    error = None
    next_url = request.GET.get('next')

    if request.method == 'POST':
        # Convertir la fecha del formato dd/mm/yyyy a yyyy-mm-dd
        data = request.POST.copy()
        if 'fecha_nacimiento' in data and data['fecha_nacimiento']:
            try:
                dia, mes, año = data['fecha_nacimiento'].split('/')
                data['fecha_nacimiento'] = f"{año}-{mes}-{dia}"
            except ValueError:
                pass
        form = EmpleadoForm(data, request.FILES, instance=empleado)
        archivos = request.FILES
        if form.is_valid():
            form.save()
            # Actualizar documentos si se suben nuevos archivos
            for req in requisitos:
                archivo = archivos.get(f'doc_{req.id}')
                if archivo and legajo:
                    doc = Documento.objects.filter(id_leg=legajo, id_requisito=req).first()
                    if doc:
                        doc.ruta_archivo = archivo
                        doc.estado_doc = True
                        doc.save()
            return redirect(next_url or 'empleados')
        else:
            return render(request, 'editar_empleado.html', {
                'form': form,
                'error': 'Por favor corrige los errores.',
                'documentos': documentos,
                'requisitos': requisitos,
                'legajo': legajo,
                'next': next_url
            })

    else:
        form = EmpleadoForm(instance=empleado)
        # Formatear la fecha de nacimiento al formato yyyy-mm-dd
        if empleado.fecha_nacimiento:
            form.initial['fecha_nacimiento'] = empleado.fecha_nacimiento.strftime('%Y-%m-%d')

    return render(request, 'editar_empleado.html', {
        'form': form,
        'documentos': documentos,
        'requisitos': requisitos,
        'legajo': legajo,
        'page_title': 'Editar Empleado',
        'next': next_url
    })

@login_required
@user_passes_test(es_admin)
def eliminar_empleado(request, id):
    empleado = get_object_or_404(Empleado, id=id)
    empleado.fecha_egreso = timezone.now().date()
    empleado.estado = 'Inactivo'
    empleado.save()
    return redirect('empleados')

from django.contrib.auth.models import Group

@login_required
@user_passes_test(es_admin)
def ver_empleados(request):
    empleados = Empleado.objects.filter(fecha_egreso__isnull=True).order_by('-fecha_ingreso', '-id')
    
    # Obtener datos para los filtros
    estado_choices = Empleado._meta.get_field('estado').choices
    cargos = Group.objects.all()

    # Paginación por defecto: 10 por página
    page = request.GET.get('page', 1)
    paginator = Paginator(empleados, 10)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return render(request, 'empleados.html', {
        'empleados': page_obj.object_list, 
        'page_obj': page_obj, 
        'paginator': paginator, 
        'page_title': 'Empleados',
        'estado_choices': estado_choices,
        'cargos': cargos
    })

@login_required
@user_passes_test(es_admin)
def buscar_empleados(request):
    query = request.GET.get('q')
    estado = request.GET.get('estado')
    cargo_id = request.GET.get('cargo')

    filters = Q(fecha_egreso__isnull=True)
    
    if query:
        filters &= (Q(nombre__icontains=query) |
                    Q(apellido__icontains=query) |
                    Q(dni__icontains=query))
    
    if estado:
        filters &= Q(estado=estado)

    if cargo_id:
        filters &= Q(user__groups__id=cargo_id)

    empleados = Empleado.objects.filter(filters).order_by('-fecha_ingreso', '-id').distinct()

    # Paginación: 10 por página
    page = request.GET.get('page', 1)
    paginator = Paginator(empleados, 10)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return render(request, 'lista_empleados.html', {'empleados': page_obj.object_list, 'page_obj': page_obj, 'paginator': paginator})

@login_required
def ver_empleado(request, id):
    empleado = get_object_or_404(Empleado, id=id)
    # Lógica de permisos:
    # Permitir si es admin O si el empleado está editando su propio perfil.
    es_propietario = hasattr(request.user, 'empleado') and request.user.empleado.id == empleado.id
    if not (es_admin(request.user) or es_propietario):
        raise PermissionDenied("No tienes permiso para ver este perfil.")
    legajo = getattr(empleado, 'legajo', None)
    documentos = Documento.objects.filter(id_leg=legajo) if legajo else []
    return render(request, 'ver_empleado.html', {
        'empleado': empleado,
        'legajo': legajo,
        'documentos': documentos,
        'page_title': 'Ver Empleado',
    })

@login_required
def ver_perfil(request):
    try:
        empleado = request.user.empleado
    except Empleado.DoesNotExist:
        # This can happen if a superuser or an admin without a linked employee profile tries to access this page.
        return redirect('home')

    legajo = getattr(empleado, 'legajo', None)
    todos_requisitos = RequisitoDocumento.objects.all()
    
    documentos_entregados = {}
    if legajo:
        # Un documento se considera entregado si tiene un archivo asociado (ruta_archivo no está vacía).
        for doc in Documento.objects.filter(id_leg=legajo).exclude(ruta_archivo=''):
            if doc.id_requisito:
                documentos_entregados[doc.id_requisito.id] = doc

    documentos_status = []
    for req in todos_requisitos:
        doc = documentos_entregados.get(req.id)
        documentos_status.append({
            'nombre': req.nombre_doc,
            'entregado': doc is not None,
            'url': doc.ruta_archivo.url if doc and doc.ruta_archivo else None
        })

    context = {
        'empleado': empleado,
        'legajo': legajo,
        'documentos_status': documentos_status,
        'page_title': 'Mi Perfil',
    }
    return render(request, 'perfil.html', context)

def link_callback(uri, rel):
    """
    Convierte URIs de HTML a rutas absolutas del sistema para que xhtml2pdf
    pueda acceder a los recursos (imágenes, etc.).
    """
    # Usa rutas de STATICFILES_DIRS si están definidas
    static_dirs = getattr(settings, 'STATICFILES_DIRS', [])
    static_url = settings.STATIC_URL
    media_url = settings.MEDIA_URL
    media_root = settings.MEDIA_ROOT

    if uri.startswith(media_url):
        path = os.path.join(media_root, uri.replace(media_url, ""))
    elif uri.startswith(static_url):
        # Busca en los directorios estáticos definidos
        path = uri.replace(static_url, "")
        for static_dir in static_dirs:
            candidate_path = os.path.join(static_dir, path)
            if os.path.exists(candidate_path):
                return candidate_path
        # Fallback a STATIC_ROOT (para entornos de producción)
        path = os.path.join(settings.STATIC_ROOT, path)
    else:
        return uri
    return path

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    response = HttpResponse(content_type='application/pdf')
    # Para descargar directamente, cambia 'inline' por 'attachment'
    response['Content-Disposition'] = f'inline; filename="perfil_{context_dict.get("empleado_id", "0")}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    if pisa_status.err:
        return HttpResponse('Tuvimos algunos errores <pre>' + html + '</pre>')
    return response

@login_required
def generar_perfil_pdf(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    # Reutilizamos la lógica de la vista de perfil para obtener el estado de los documentos
    legajo = getattr(empleado, 'legajo', None)
    documentos_entregados_ids = Documento.objects.filter(id_leg=legajo, estado_doc=True).values_list('id_requisito_id', flat=True) if legajo else []
    documentos_status = [{
        'nombre': req.nombre_doc,
        'entregado': req.id in documentos_entregados_ids
    } for req in RequisitoDocumento.objects.all()]
    context = {'empleado': empleado, 'documentos_status': documentos_status, 'empleado_id': empleado_id}
    return render_to_pdf('perfil_pdf.html', context)

@login_required
@user_passes_test(es_admin)
def generar_lista_empleados_pdf(request):
    # Por ahora, imprime todos los empleados activos. Se podría extender para usar filtros.
    empleados = Empleado.objects.filter(estado='Activo').order_by('apellido', 'nombre')
    context = {'empleados': empleados}
    return render_to_pdf('lista_empleados_pdf.html', context)

# --- Gráfico de barras empleados activos/inactivos ---
@login_required
@user_passes_test(es_admin)
def grafico_empleados_activos_inactivos(request):
    empleados = Empleado.objects.values('estado')
    df = pd.DataFrame(list(empleados))
    conteo = df['estado'].value_counts().reset_index()
    conteo.columns = ['Estado', 'Cantidad']
    fig = px.bar(conteo, x='Estado', y='Cantidad', title='Empleados Activos vs Inactivos', text='Cantidad')
    fig.update_traces(textposition='outside')
    grafico_html = fig.to_html(full_html=False)
    return render(request, 'grafico_empleados.html', {'grafico': grafico_html})

# --- Exportar gráfico a PDF ---
@login_required
@user_passes_test(es_admin)
def grafico_empleados_pdf(request):
    empleados = Empleado.objects.values('estado')
    df = pd.DataFrame(list(empleados))
    conteo = df['estado'].value_counts().reset_index()
    conteo.columns = ['Estado', 'Cantidad']
    fig = px.bar(conteo, x='Estado', y='Cantidad', title='Empleados Activos vs Inactivos', text='Cantidad')
    fig.update_traces(textposition='outside')
    grafico_html = fig.to_html(full_html=False)

    template = get_template('grafico_empleados_pdf.html')
    html = template.render({'grafico': grafico_html})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="grafico_empleados.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error al generar PDF', status=500)
    return response

@login_required
def dashboard(request):
    if not es_admin(request.user):
        return redirect('ver_perfil')

    today = date.today()

    # Card data
    total_empleados = Empleado.objects.filter(estado='Activo').count()
    asistencia_hoy = Asistencia.objects.filter(fecha_hora__date=today).count()
    sanciones_mes = SancionEmpleado.objects.filter(fecha_inicio__month=today.month, fecha_inicio__year=today.year).count()
    contrataciones_mes = Empleado.objects.filter(fecha_ingreso__month=today.month, fecha_ingreso__year=today.year).count()

    # Hires chart (last 6 months)
    hires_labels = []
    hires_data = []
    for i in range(5, -1, -1):
        year = today.year
        month = today.month - i
        if month <= 0:
            month += 12
            year -= 1
        
        hires_labels.append(_(calendar.month_name[month]))
        
        count = Empleado.objects.filter(fecha_ingreso__year=year, fecha_ingreso__month=month).count()
        hires_data.append(count)

    # Status chart
    status_data = Empleado.objects.values('estado').annotate(count=Count('id'))
    status_labels = [item['estado'] for item in status_data]
    status_values = [item['count'] for item in status_data]

    # Recent incidents
    ultimos_incidentes = IncidenteEmpleado.objects.select_related('id_empl', 'id_incidente').order_by('-fecha_ocurrencia')[:5]

    # Recent activity (notifications)
    actividad_reciente = Notificacion.objects.order_by('-fecha_creacion')[:5]

    context = {
        'total_empleados': total_empleados,
        'asistencia_hoy': asistencia_hoy,
        'sanciones_mes': sanciones_mes,
        'contrataciones_mes': contrataciones_mes,
        'page_title': 'Inicio',
        'hires_labels': json.dumps(hires_labels),
        'hires_data': json.dumps(hires_data),
        'status_labels': json.dumps(status_labels),
        'status_data': json.dumps(status_values),
        'ultimos_incidentes': ultimos_incidentes,
        'actividad_reciente': actividad_reciente,
    }
    return render(request, 'dashboard.html', context)

@login_required
def employee_dashboard(request):
    if request.user.is_staff:
        # Maybe redirect to admin dashboard or show a message
        pass
    return render(request, 'dashboard_empleado.html', {'page_title': 'Dashboard Empleado'})

@login_required
def switch_to_employee_view(request):
    if not es_admin(request.user):
        return redirect('mi_perfil')

    # An admin wants to switch to an employee view.
    # We'll try to find an employee profile linked to the admin user.
    employee_profile = getattr(request.user, 'empleado', None)

    if employee_profile:
        request.session['view_as_employee_id'] = employee_profile.id
    else:
        # If the admin user doesn't have a linked employee profile, fall back to the first employee.
        # This is placeholder behavior; a better UX might be to select an employee to view as.
        first_employee = Empleado.objects.first()
        if first_employee:
            request.session['view_as_employee_id'] = first_employee.id

    # Add a cache-busting timestamp to prevent browser caching issues
    # redirect_url = f"{reverse('employee_dashboard')}?_t={int(timezone.now().timestamp())}"
    return redirect('ver_perfil')

@login_required
def switch_to_admin_view(request):
    if 'view_as_employee_id' in request.session:
        del request.session['view_as_employee_id']
    
    # Add a cache-busting timestamp to prevent browser caching issues
    redirect_url = f"{reverse('home')}?_t={int(timezone.now().timestamp())}"
    return redirect(redirect_url)