from empleados.models import Notificacion

def notificaciones_processor(request):
    if request.user.is_authenticated:
        notificaciones_no_leidas = Notificacion.objects.filter(id_user=request.user, leida=False)
        return {
            'notificaciones_no_leidas': notificaciones_no_leidas,
            'notificaciones_count': notificaciones_no_leidas.count(),
        }
    return {
        'notificaciones_no_leidas': [],
        'notificaciones_count': 0,
    }