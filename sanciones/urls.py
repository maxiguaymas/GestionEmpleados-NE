from django.urls import path
from . import views

urlpatterns = [
    # ver sanciones de un empleado
    path('ver/<int:empleado_id>/', views.sanciones_empleado, name='sanciones_empleado'),
    path('agregar/', views.agregar_sancion_empleado, name='agregar_sancion_empleado'),
    path('aplicar-masiva/incidente/<int:incidente_id>/', views.aplicar_sancion_masiva, name='aplicar_sancion_masiva'),
    path('ver/', views.ver_todas_sanciones, name='ver_todas_sanciones'),
    path('resolucion/agregar/<int:sancion_empleado_id>/', views.agregar_resolucion, name='agregar_resolucion'),
    path('detalle/<int:sancion_id>/', views.detalle_sancion, name='detalle_sancion'),
    path('mis-sanciones/', views.mis_sanciones, name='mis_sanciones'),
]