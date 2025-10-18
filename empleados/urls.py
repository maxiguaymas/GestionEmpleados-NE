from django.urls import path
from . import views

urlpatterns = [
    path('inicio/', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # path('empleados/', views.empleados, name='empleados'),
    path('crear/', views.crear_empleado, name='crear_empleado'),
    path('editar/<int:id>/', views.editar_empleado, name='editar_empleado'),
    path('eliminar/<int:id>/', views.eliminar_empleado, name='eliminar_empleado'),
    path('ver/', views.ver_empleados, name='empleados'), # Renombrado de ver_empleados a empleados
    path('ver/<int:id>/', views.ver_empleado, name='ver_empleado'),
    path('buscar/', views.buscar_empleados, name='buscar_empleados'),
    path('perfil/', views.ver_perfil, name='ver_perfil'),
    path('perfil/pdf/<int:empleado_id>/', views.generar_perfil_pdf, name='generar_perfil_pdf'),
    path('lista/pdf/', views.generar_lista_empleados_pdf, name='generar_lista_empleados_pdf'),
    path('grafico-empleados/', views.grafico_empleados_activos_inactivos, name='grafico_empleados'),
    path('grafico-empleados/pdf/', views.grafico_empleados_pdf, name='grafico_empleados_pdf'),
    path('switch-to-employee/', views.switch_to_employee_view, name='switch_to_employee_view'),
    path('switch-to-admin/', views.switch_to_admin_view, name='switch_to_admin_view'),
]