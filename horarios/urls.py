from django.urls import path
from . import views

urlpatterns = [
    # Vista principal del admin de horarios
    path('', views.horarios_admin, name='horarios_admin'),
    
    # Procesamiento de los formularios de creación
    path('crear/', views.crear_horario, name='crear_horario'),
    path('editar/<int:horario_id>/', views.editar_horario, name='editar_horario'),
    path('eliminar/<int:horario_id>/', views.eliminar_horario, name='eliminar_horario'),
    
    # Procesamiento del formulario de asignación
    path('asignar/', views.asignar_horario, name='asignar_horario'),
    
    # Endpoint para la UI dinámica de asignación
    path('api/get-empleados/<int:horario_id>/', views.get_empleados_por_horario, name='get_empleados_por_horario'),
    path('api/historial/', views.historial_api_view, name='historial_api'),

    # Vistas para los empleados
    path('mis-horarios/', views.mis_horarios_empleado, name='mis_horarios_empleado'),
    path('ver/<int:empleado_id>/', views.ver_horarios_empleado, name='ver_horarios_empleado'),

    # Rutas antiguas (opcional, se pueden eliminar o redirigir si ya no se usan)
    path('ver/', views.ver_horarios_asig, name='ver_horarios_asig'),
    # path('ver/<int:id>/', views.mis_horarios, name='mis_horarios'),
]
