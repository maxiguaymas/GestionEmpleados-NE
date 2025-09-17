from empleados.models import Notificacion

def notificaciones_processor(request):
    """
    Agrega las notificaciones no leídas y su conteo al contexto de la plantilla.
    """
    if request.user.is_authenticated:
        notificaciones_no_leidas = request.user.notificaciones.filter(leida=False)
        return {
            'notificaciones': notificaciones_no_leidas,
            'notificaciones_sin_leer_count': notificaciones_no_leidas.count()
        }
    return {}


