from .models import Empleado

def view_mode_processor(request):
    context = {
        'view_as_employee': None,
        'original_user': request.user
    }
    view_as_employee_id = request.session.get('view_as_employee_id')

    if view_as_employee_id:
        try:
            employee = Empleado.objects.select_related('user').get(pk=view_as_employee_id)
            context['view_as_employee'] = employee
        except Empleado.DoesNotExist:
            if 'view_as_employee_id' in request.session:
                del request.session['view_as_employee_id']
    
    return context
