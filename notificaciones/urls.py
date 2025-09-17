from django.urls import path
from . import views

urlpatterns = [
    path('marcar-leida/<int:notificacion_id>/', views.marcar_notificacion_leida, name='marcar_leida'),
    path('todas/', views.ver_todas_notificaciones, name='ver_todas_notificaciones'),
]