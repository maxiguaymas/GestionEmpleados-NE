from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from empleados.models import Recibo_Sueldos as Recibo, Empleado, Notificacion
from .forms import ReciboSueldoForm
from empleados.views import es_admin
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse
from django.template.loader import render_to_string
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

            # Enviar correo electrónico
            try:
                # Imprimimos el email del destinatario para verificarlo
                print(f"Intentando enviar correo de notificación a: {empleado.email}")
                
                # Construir la URL absoluta para el logo y el portal
                logo_url = request.build_absolute_uri(settings.STATIC_URL + 'images/logo-nuevas-energias-v2.png')
                portal_url = request.build_absolute_uri(reverse('mis_recibos'))

                asunto = f"Nuevo recibo de sueldo disponible: Período {recibo.periodo}"
                
                # Mensaje en texto plano como alternativa
                cuerpo_mensaje_plain = (
                    f"Hola {empleado.nombre},\n\n"
                    f"Te informamos que tu recibo de sueldo para el período {recibo.periodo} ya está disponible en el portal de empleados.\n\n"
                    f"Puedes verlo ingresando a la sección 'Mis Recibos' en la siguiente dirección: {portal_url}\n\n"
                    "Saludos,\n"
                    "Equipo de RRHH"
                )

                # Renderizar el template HTML
                cuerpo_mensaje_html = render_to_string('email/notificacion_recibo.html', {
                    'empleado_nombre': empleado.nombre,
                    'periodo': recibo.periodo,
                    'logo_url': logo_url,
                    'portal_url': portal_url,
                })
                send_mail(asunto, cuerpo_mensaje_plain, settings.DEFAULT_FROM_EMAIL, [empleado.email], html_message=cuerpo_mensaje_html)
                # Mensaje de éxito en la consola
                print(f"Correo de notificación enviado exitosamente a {empleado.email}")
            except Exception as e:
                # Imprime el error en la consola para depuración
                print(f"ERROR al enviar correo: {e}")
                messages.warning(request, f"El recibo se guardó, pero hubo un error al enviar el correo de notificación: {e}")

            messages.success(request, "Recibo cargado correctamente.")
            return redirect('recibos_admin')
    else:
        form = ReciboSueldoForm()
    return render(request, 'recibos.html', {'form': form, 'page_title': 'Cargar Recibo'})

@user_passes_test(es_admin)
def recibos_admin(request):
    form = ReciboSueldoForm()
    return render(request, 'recibos.html', {'form': form, 'page_title': 'Recibos'})

@user_passes_test(es_admin)
def editar_recibo(request, recibo_id):
    recibo = get_object_or_404(Recibo, id=recibo_id)
    if request.method == 'POST':
        # We pass instance=recibo to tell the form we are editing an existing object.
        form = ReciboSueldoForm(request.POST, request.FILES, instance=recibo)
        if form.is_valid():
            form.save()
            messages.success(request, "Recibo actualizado correctamente.")
            return redirect('recibos_admin')
        else:
            messages.error(request, "Error al actualizar el recibo. Por favor, revise los datos.")
    # This part is not really used since the modal is populated via API, but good practice.
    return redirect('recibos_admin')

def mis_recibos(request):
    try:
        empleado = request.user.empleado
        recibos = Recibo.objects.filter(id_empl=empleado).order_by('-fecha_emision')
        
        # Lógica de filtrado
        mes = request.GET.get('mes')
        anio = request.GET.get('anio')
        
        years = Recibo.objects.filter(id_empl=empleado).dates('fecha_emision', 'year').distinct()
        
        if anio:
            recibos = recibos.filter(fecha_emision__year=anio)
        if mes:
            recibos = recibos.filter(fecha_emision__month=mes)

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
        'page_title': 'Mis Recibos',
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
        'page_title': 'Recibos del Empleado',
    })

def api_ver_recibos_empleado(request, dni):
    try:
        empleado = Empleado.objects.get(dni=dni)
        recibos = Recibo.objects.filter(id_empl=empleado).order_by('-fecha_emision')

        # Lógica de filtrado
        mes = request.GET.get('mes')
        anio = request.GET.get('anio')

        years = Recibo.objects.filter(id_empl=empleado).dates('fecha_emision', 'year').distinct()

        if mes and anio:
            recibos = recibos.filter(fecha_emision__month=mes, fecha_emision__year=anio)
            
        data = {
            'status': 'success',
            'empleado': {
                'nombre': empleado.nombre,
                'apellido': empleado.apellido,
            },
            'recibos': list(recibos.values('id', 'fecha_emision', 'periodo', 'ruta_pdf', 'ruta_imagen')),
            'years': [year.year for year in years]
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

def api_get_recibo_details(request, recibo_id):
    try:
        recibo = Recibo.objects.get(id=recibo_id)
        data = {
            'status': 'success',
            'recibo': {
                'id': recibo.id, 
                'id_empl_id': recibo.id_empl.id, 
                'fecha_emision': recibo.fecha_emision, 
                'periodo': recibo.periodo,
                'ruta_pdf_url': recibo.ruta_pdf.url if recibo.ruta_pdf else None,
                'ruta_imagen_url': recibo.ruta_imagen.url if recibo.ruta_imagen else None,
            }
        }
        return JsonResponse(data)
    except Recibo.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Recibo no encontrado.'}, status=404)
