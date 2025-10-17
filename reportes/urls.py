from django.urls import path
from . import views

urlpatterns = [
    path('', views.reportes_home, name='reportes_home'),
    path('estado_empleados/', views.reporte_estado_empleados, name='reporte_estado_empleados'),
    path('sanciones_por_tipo/', views.reportes_sanciones_por_tipo, name='reporte_sanciones_por_tipo'),
    path('incidentes_por_tipo/', views.reporte_incidentes_por_tipo, name='reporte_incidentes_por_tipo'),

    # Endpoints de datos para los gráficos
    path('data/estado_empleados/', views.reporte_estado_empleados_data, name='reporte_estado_empleados_data'),
    path('data/sanciones/', views.reporte_sanciones_data, name='reporte_sanciones_data'),
    path('data/incidentes/', views.reporte_incidentes_data, name='reporte_incidentes_data'),
]