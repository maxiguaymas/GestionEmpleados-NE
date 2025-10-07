from django.shortcuts import get_object_or_404, render, redirect
from .forms import HorarioForm, HorarioPresetForm, AsignarHorarioForm
from empleados.models import Horarios, Empleado, AsignacionHorario
from django.contrib import messages
from empleados.views import es_admin
from django.contrib.auth.decorators import user_passes_test, login_required
from django.http import JsonResponse
from django.db.models import Count

@user_passes_test(es_admin)
def horarios_admin(request):
    """
    Vista principal para la gestión de horarios por parte del administrador.
    Renderiza una plantilla que contiene varias pestañas (tabs) para:
    1. Ver asignaciones actuales.
    2. Asignar horarios a empleados.
    3. Crear nuevos horarios (predefinidos o personalizados).
    """
    # Anotamos la cantidad de personal asignado a cada horario
    horarios_con_conteo = Horarios.objects.annotate(
        personal_asignado=Count('asignaciones')
    )

    context = {
        # Para la pestaña "Ver Asignaciones"
        'horarios_con_conteo': horarios_con_conteo,
        'asignaciones': AsignacionHorario.objects.select_related('id_empl', 'id_horario').all(),

        # Para la pestaña "Asignar Horarios"
        'horarios_todos': Horarios.objects.all(),
        'empleados_activos': Empleado.objects.filter(estado='Activo'),

        # Para la pestaña "Crear Horario"
        'preset_form': HorarioPresetForm(),
        'custom_form': HorarioForm(),
        'page_title': 'Horarios',
    }
    return render(request, 'horarios.html', context)

@user_passes_test(es_admin)
def crear_horario(request):
    """
    Procesa la creación de nuevos horarios.
    Distingue si se está creando un horario desde una plantilla (preset)
    o un horario personalizado, basándose en el nombre del botón de submit.
    """
    if request.method == 'POST':
        if 'submit_preset' in request.POST:
            form = HorarioPresetForm(request.POST)
            if form.is_valid():
                horario = form.save()
                messages.success(request, f'Horario "{horario.nombre}" creado/actualizado con éxito.')
            else:
                # Si hay errores, es mejor mostrarlos en el formulario.
                # Esta implementación simple solo muestra un error genérico.
                messages.error(request, 'Error al crear el horario predefinido. Por favor, verifique los datos.')
        
        elif 'submit_custom' in request.POST:
            form = HorarioForm(request.POST)
            if form.is_valid():
                horario = form.save()
                messages.success(request, f'Horario personalizado "{horario.nombre}" creado con éxito.')
            else:
                # Idealmente, renderizaríamos el form con errores.
                # Por simplicidad, redirigimos con un mensaje de error.
                error_msg = 'Error al crear el horario personalizado. ' + ' '.join([f'{k}: {v[0]}' for k, v in form.errors.items()])
                messages.error(request, error_msg)

    return redirect('horarios_admin')

from django.shortcuts import get_object_or_404, render, redirect
from .forms import HorarioForm, HorarioPresetForm, AsignarHorarioForm
from empleados.models import Horarios, Empleado, AsignacionHorario, Notificacion
from django.contrib import messages
from empleados.views import es_admin
from django.contrib.auth.decorators import user_passes_test, login_required
from django.http import JsonResponse
from django.db.models import Count
from django.urls import reverse

@user_passes_test(es_admin)
def asignar_horario(request):
    """
    Procesa la asignación de múltiples empleados a un horario específico.
    También puede desasignar a todos los empleados de ese horario si la lista
    de empleados viene vacía.
    """
    if request.method == 'POST':
        horario_id = request.POST.get('horario_id')
        # getlist para recibir una lista de IDs de empleados
        empleados_ids = request.POST.getlist('empleados')

        if not horario_id:
            messages.error(request, 'No se seleccionó un horario.')
            return redirect('horarios_admin')

        horario = get_object_or_404(Horarios, id=horario_id)

        # Obtenemos las asignaciones actuales para este horario
        asignaciones_actuales = AsignacionHorario.objects.filter(id_horario=horario)
        empleados_actuales_ids = set(map(str, asignaciones_actuales.values_list('id_empl_id', flat=True)))
        
        empleados_nuevos_ids = set(empleados_ids)

        # 1. Empleados a desasignar (estaban antes pero no en la nueva lista)
        empleados_a_quitar_ids = empleados_actuales_ids - empleados_nuevos_ids
        if empleados_a_quitar_ids:
            AsignacionHorario.objects.filter(id_horario=horario, id_empl_id__in=empleados_a_quitar_ids).delete()

        # 2. Empleados a asignar (están en la nueva lista pero no estaban antes)
        empleados_a_anadir_ids = empleados_nuevos_ids - empleados_actuales_ids
        if empleados_a_anadir_ids:
            empleados_a_asignar = Empleado.objects.filter(id__in=empleados_a_anadir_ids)
            nuevas_asignaciones = [
                AsignacionHorario(id_empl=empleado, id_horario=horario)
                for empleado in empleados_a_asignar
            ]
            AsignacionHorario.objects.bulk_create(nuevas_asignaciones)

            # Create notifications for newly assigned employees
            link = reverse('mis_horarios_empleado')
            for empleado in empleados_a_asignar:
                mensaje = f"Se te ha asignado un nuevo horario: {horario.nombre}."
                Notificacion.objects.create(
                    id_user=empleado.user,
                    mensaje=mensaje,
                    enlace=link
                )

        messages.success(request, f'Se actualizaron las asignaciones para el horario "{horario.nombre}".')
        return redirect('horarios_admin')

    return redirect('horarios_admin')

@user_passes_test(es_admin)
def ver_horarios_asig(request):
    # Esta vista ya no es necesaria si todo se maneja en horarios_admin,
    # pero la mantenemos por si hay alguna URL que apunte aquí.
    return redirect('horarios_admin')

@login_required
def mis_horarios_empleado(request):
    """
    Muestra los horarios asignados al empleado que ha iniciado sesión.
    """
    try:
        empleado = request.user.empleado
        # Filtramos todas las asignaciones activas
        asignaciones = AsignacionHorario.objects.filter(id_empl=empleado, estado=True).select_related('id_horario')
    except Empleado.DoesNotExist:
        asignaciones = []
    
    context = {
        'asignaciones': asignaciones,
        'page_title': 'Mis Horarios',
    }
    return render(request, 'mis_horarios.html', context)

# API endpoint para obtener los empleados de un horario (para la UI de asignar)
@user_passes_test(es_admin)
def get_empleados_por_horario(request, horario_id):
    """
    Endpoint de API para obtener los empleados asignados a un horario
    y los que están disponibles.
    """
    horario = get_object_or_404(Horarios, id=horario_id)
    
    empleados_asignados = Empleado.objects.filter(asignaciones_horario__id_horario=horario, estado='Activo')
    ids_asignados = empleados_asignados.values_list('id', flat=True)
    
    empleados_disponibles = Empleado.objects.filter(estado='Activo').exclude(id__in=ids_asignados)

    return JsonResponse({
        'asignados': list(empleados_asignados.values('id', 'nombre', 'apellido')),
        'disponibles': list(empleados_disponibles.values('id', 'nombre', 'apellido')),
    })

@login_required
def ver_horarios_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    asignaciones = AsignacionHorario.objects.filter(id_empl=empleado).select_related('id_horario').order_by('-fecha_asignacion')
    context = {
        'empleado': empleado,
        'asignaciones': asignaciones,
        'page_title': 'Horarios del Empleado',
    }
    return render(request, 'ver_horarios_empleado.html', context)
