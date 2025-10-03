from django.urls import path
from .views import reporte_estado_empleados, reportes_home, reportes_sanciones_por_tipo, reporte_incidentes_por_tipo

urlpatterns = [
    path('', reportes_home, name='reportes_home'),
    path('estado_empleados/', reporte_estado_empleados, name='reporte_estado_empleados'),
    path('sanciones_por_tipo/', reportes_sanciones_por_tipo, name='reporte_sanciones_por_tipo'),
    path('incidentes_por_tipo/', reporte_incidentes_por_tipo, name='reporte_incidentes_por_tipo'),
]
