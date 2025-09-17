from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """
    Verifica si un usuario pertenece a un grupo específico.
    """
    return user.groups.filter(name__iexact=group_name).exists()

@register.filter(name='get_initials')
def get_initials(empleado):
    """
    Obtiene las iniciales de un objeto Empleado.
    """
    if empleado and hasattr(empleado, 'nombre') and hasattr(empleado, 'apellido'):
        if empleado.nombre and empleado.apellido:
            return (empleado.nombre[0] + empleado.apellido[0]).upper()
        elif empleado.nombre:
            return empleado.nombre[0].upper()
    return 'E' # Default for Empleado

@register.filter(name='get_user_initials')
def get_user_initials(user):
    """
    Obtiene las iniciales de un objeto User.
    """
    if user.first_name and user.last_name:
        return (user.first_name[0] + user.last_name[0]).upper()
    elif user.first_name:
        return user.first_name[0].upper()
    elif user.username:
        return user.username[:2].upper()
    return 'U' # Default for User
