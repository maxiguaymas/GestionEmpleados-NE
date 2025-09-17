from django.urls import path
from . import views

urlpatterns = [
    path('', views.asistencia_admin, name='asistencia_admin'),
    path('registrar-rostro/', views.vista_registrar_rostro, name='registrar_rostro'),
    path('marcar-asistencia/', views.vista_marcar_asistencia, name='marcar_asistencia'),
    # URLs de la API
    path('api/guardar-rostro/', views.api_guardar_rostro, name='api_guardar_rostro'),
    path('api/reconocer-rostro/', views.api_reconocer_rostro, name='api_reconocer_rostro'),
    path('api/ver-asistencias/<int:dni>/', views.api_ver_asistencias_empleado, name='api_ver_asistencias_empleado'),
    path('ver/<int:empleado_id>/', views.ver_asistencias_empleado, name='ver_asistencias_empleado'),
    path('mis-asistencias/', views.mis_asistencias, name='mis_asistencias'),
]