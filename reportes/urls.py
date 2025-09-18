from django.urls import path
from .views import GenerarReporteAsistencia

urlpatterns = [
    path('asistencia/', GenerarReporteAsistencia.as_view(), name='reporte_asistencia'),
]
