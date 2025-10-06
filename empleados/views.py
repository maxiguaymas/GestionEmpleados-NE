from django.shortcuts import render
from asistencia.models import Asistencia
from .models import SancionEmpleado
from datetime import date
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .forms import EmpleadoForm
from .models import Empleado, Notificacion
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test
from empleados.models import Legajo, Documento, RequisitoDocumento

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
            user = User.objects.create_user(username=str(dni), password=str(dni))
            user.groups.add(grupo)
            user.save()
            empleado.user = user
            empleado.save()

            # Crear notificación de bienvenida para el nuevo empleado
            Notificacion.objects.create(
                id_user=user,
                mensaje=f"¡Bienvenido/a, {empleado.nombre}! Tu perfil ha sido creado exitosamente.",
                enlace=reverse('ver_empleado', args=[empleado.id])
            )

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

    if request.method == 'POST':
        form = EmpleadoForm(request.POST, request.FILES, instance=empleado)
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
            return redirect('empleados')
        else:
            return render(request, 'editar_empleado.html', {
                'form': form,
                'error': 'Por favor corrige los errores.',
                'documentos': documentos,
                'requisitos': requisitos,
                'legajo': legajo,
            })

    else:
        form = EmpleadoForm(instance=empleado)

    return render(request, 'editar_empleado.html', {
        'form': form,
        'documentos': documentos,
        'requisitos': requisitos,
        'legajo': legajo,
        'page_title': 'Editar Empleado',
    })

@login_required
@user_passes_test(es_admin)
def eliminar_empleado(request, id):
    empleado = get_object_or_404(Empleado, id=id)
    empleado.fecha_egreso = timezone.now().date()
    empleado.estado = 'Inactivo'
    empleado.save()
    return redirect('ver_empleados')

@login_required
@user_passes_test(es_admin)
def ver_empleados(request):
    empleados = Empleado.objects.filter(fecha_egreso__isnull=True)
    return render(request, 'empleados.html', {'empleados': empleados, 'page_title': 'Empleados'})

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
    total_empleados = Empleado.objects.filter(estado='Activo').count()
    asistencia_hoy = Asistencia.objects.filter(fecha_hora__date=date.today()).count()
    
    today = date.today()
    sanciones_mes = SancionEmpleado.objects.filter(fecha_inicio__month=today.month, fecha_inicio__year=today.year).count()

    context = {
        'total_empleados': total_empleados,
        'asistencia_hoy': asistencia_hoy,
        'sanciones_mes': sanciones_mes,
        'page_title': 'Dashboard',
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