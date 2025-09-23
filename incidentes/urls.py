from django.urls import path
from . import views

urlpatterns = [
    path('registrar/', views.registrar_incidente, name='registrar_incidente'),
    path('ver/', views.ver_incidentes, name='ver_incidentes'),
    path('detalle/<int:incidente_id>/', views.detalle_incidente, name='detalle_incidente'),
    # URL para ver los incidentes de un empleado específico
    path('empleado/<int:empleado_id>/', views.ver_incidentes_empleado, name='incidentes_empleado'),
    path('mis-incidentes/', views.mis_incidentes, name='mis_incidentes'),
    path('corregir/<int:incidente_id>/', views.corregir_incidente, name='corregir_incidente'),
    path('resolver/<int:incidente_id>/', views.resolver_incidente, name='resolver_incidente'),
]