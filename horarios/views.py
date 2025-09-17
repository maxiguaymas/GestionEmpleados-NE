from django.shortcuts import get_object_or_404, render, redirect
from .forms import HorarioForm
from empleados.models import Horarios,Empleado,AsignacionHorario
from django.contrib import messages
from empleados.views import es_admin
from django.contrib.auth.decorators import user_passes_test, login_required

# Create your views here.
@user_passes_test(es_admin)
def cargar_horario(request):
    if request.method == 'POST':
        form = HorarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('horarios_admin')
    else:
        form = HorarioForm()
    return render(request, 'cargar_horario.html', {'form': form})

@user_passes_test(es_admin)
def asignar_horario(request):
    horarios = Horarios.objects.all()
    empleados = Empleado.objects.all()
    
    

    if request.method == 'POST':
        asignaciones_realizadas = 0
        for horario in horarios:
            for i in range(1, horario.cantidad_personal + 1):
                empleado_id = request.POST.get(f"empleado_{horario.id}_{i}")
                if empleado_id:
                    empleado = Empleado.objects.get(id=empleado_id)
                    # Evita asignaciones duplicadas
                    if not AsignacionHorario.objects.filter(id_empl=empleado, id_horario=horario).exists():
                        AsignacionHorario.objects.create(
                            id_empl=empleado,
                            id_horario=horario,
                            estado=True
                        )
                        asignaciones_realizadas += 1
        if asignaciones_realizadas:
            messages.success(request, f"{asignaciones_realizadas} asignaciones realizadas correctamente.")
        else:
            messages.info(request, "No se realizaron nuevas asignaciones.")
        return redirect('horarios_admin')


    return render(request, 'asignar_horario.html', {
        'horarios': horarios,
        'empleados': empleados,
    })

@user_passes_test(es_admin)
def ver_horarios_asig(request):
    """
    Muestra una tabla con todos los horarios asignados a todos los empleados.
    La plantilla utiliza DataTables para permitir la bÃºsqueda y paginaciÃ³n.
    """
    # Obtenemos todas las asignaciones y optimizamos la consulta con select_related
    horarios = AsignacionHorario.objects.all().select_related('id_empl', 'id_horario')
    return render(request, 'ver_horarios_asig.html', {
        'horarios': horarios,
    })

def mis_horarios(request, id):
    # Solo permitir acceso a usuarios logeados
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesiÃ³n para ver los horarios asignados.")
        return redirect('login')
    mensaje = ""
    empleado = get_object_or_404(Empleado, id=id)
    print(empleado)
    horarios = AsignacionHorario.objects.filter(id_empl=empleado).select_related('id_empl', 'id_horario')
    # print(horarios)
    if not horarios:
        mensaje = "No hay horarios asignados para este empleado."
    
    return render(request, 'mis_horarios.html', {
        'horarios': horarios,
        'mensaje': mensaje,
    })

@user_passes_test(es_admin)
def horarios_admin(request):
    # Context for ver_horarios_asig_tab
    horarios_asignados = AsignacionHorario.objects.all().select_related('id_empl', 'id_horario')
    
    # Context for asignar_horario_tab
    horarios_todos = Horarios.objects.all()
    empleados_todos = Empleado.objects.all()
    
    # Context for cargar_horario_tab
    form = HorarioForm()

    context = {
        'horarios': horarios_asignados,
        'horarios_todos': horarios_todos,
        'empleados': empleados_todos,
        'form': form,
    }
    return render(request, 'horarios.html', context)

@login_required
def mis_horarios_empleado(request):
    try:
        empleado = request.user.empleado
        asignacion = AsignacionHorario.objects.filter(id_empl=empleado).select_related('id_horario').first()
    except Empleado.DoesNotExist:
        asignacion = None
    
    context = {
        'asignacion': asignacion,
    }
    return render(request, 'mis_horarios.html', context)
