from django.urls import path
from .views import reporte_estado_empleados, reportes_home

urlpatterns = [
    path('', reportes_home, name='reportes_home'),
    path('estado_empleados/', reporte_estado_empleados, name='reporte_estado_empleados'),
]
