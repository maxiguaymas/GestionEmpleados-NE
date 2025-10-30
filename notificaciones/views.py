from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from empleados.models import Notificacion

@login_required
def centro_notificaciones(request):
    # Al visitar el centro, actualizamos las no leídas a leídas.
    # Guardamos los IDs antes de actualizar para poder destacarlas en la plantilla si es necesario.
    no_leidas_ids = list(Notificacion.objects.filter(id_user=request.user, leida=False).values_list('id', flat=True))
    
    Notificacion.objects.filter(id__in=no_leidas_ids).update(leida=True)

    notificaciones_list = Notificacion.objects.filter(id_user=request.user)

    return render(request, 'centro_notificaciones.html', {
        'notificaciones_list': notificaciones_list,
        'just_read_ids': no_leidas_ids, # Pasamos los IDs a la plantilla
        'page_title': 'Notificaciones'
    })

@login_required
def marcar_todas_como_leidas(request):
    Notificacion.objects.filter(id_user=request.user, leida=False).update(leida=True)
    # Redirigimos de vuelta a la página desde la que se hizo la petición
    return redirect(request.META.get('HTTP_REFERER', 'notificaciones:centro_notificaciones'))