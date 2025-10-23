from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def break_long_words(value, max_len=25):
    """
    Inserta un espacio de ancho cero en palabras largas para permitir el corte de línea.
    """
    if not isinstance(value, str):
        value = str(value)

    # Usamos una expresión regular para encontrar secuencias de caracteres sin espacios
    # que sean más largas que max_len.
    def insert_breaks(match):
        word = match.group(0)
        # Insertamos el espacio de ancho cero cada max_len caracteres
        return ''.join([word[i:i+max_len] + '&#8203;' for i in range(0, len(word), max_len)])

    # La expresión regular busca secuencias de caracteres que no sean espacios en blanco
    # y que tengan una longitud de al menos max_len.
    long_word_regex = re.compile(r'[^\s]{' + str(max_len) + r',}')

    # Aplicamos la función de inserción a todas las coincidencias
    broken_value = long_word_regex.sub(insert_breaks, value)

    return mark_safe(broken_value)

@register.simple_tag
def get_group_color_classes(group_name):
    """
    Devuelve las clases de Tailwind CSS correspondientes a un nombre de grupo.
    """
    color_map = {
        'Administrador': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
        'Empleado': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
        'RRHH': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
        'Tecnico': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
        # Puedes añadir más grupos y colores aquí
    }
    # Color por defecto si el grupo no está en el mapa
    default_classes = 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
    return color_map.get(group_name, default_classes)
