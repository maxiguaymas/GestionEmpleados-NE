from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from empleados.models import Notificacion

@login_required
def marcar_notificacion_leida(request, notificacion_id):
    """
    Marca una notificación específica como leída y redirige al usuario
    al enlace original de la notificación.
    """
    # Buscamos la notificación, asegurando que pertenezca al usuario logueado.
    # Si no se encuentra o no pertenece al usuario, devuelve un 404.
    notificacion = get_object_or_404(Notificacion, id=notificacion_id, destinatario=request.user)

    # Si la encontramos y no está leída, la marcamos como leída.
    if not notificacion.leida:
        notificacion.leida = True
        notificacion.save()

    # Redirigimos al enlace original o a una página por defecto si no hay enlace.
    return redirect(notificacion.enlace or 'home')

@login_required
def ver_todas_notificaciones(request):
    """
    Muestra todas las notificaciones (leídas y no leídas) del usuario.
    """
    # Usamos el related_name 'notificaciones' que definimos en el modelo.
    todas_las_notificaciones = request.user.notificaciones.all()
    return render(request, 'todas_las_notificaciones.html', {'todas_las_notificaciones': todas_las_notificaciones})
