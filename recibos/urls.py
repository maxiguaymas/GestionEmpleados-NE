from django.urls import path
from . import views

urlpatterns = [
    path('', views.recibos_admin, name='recibos_admin'),
    path('cargar/', views.cargar_recibo, name='cargar_recibo'),
    path('mis-recibos/', views.mis_recibos, name='mis_recibos'),
    path('api/ver-recibos/<int:dni>/', views.api_ver_recibos_empleado, name='api_ver_recibos_empleado'),
    path('ajax/buscar-empleado/', views.ajax_buscar_empleado, name='ajax_buscar_empleado'),
    path('empleado/<int:empleado_id>/', views.ver_recibos_empleado, name='ver_recibos_empleado'),
]