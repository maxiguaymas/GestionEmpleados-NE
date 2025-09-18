from django.urls import path
from . import views

app_name = 'notificaciones'

urlpatterns = [
    path('', views.centro_notificaciones, name='centro_notificaciones'),
    path('marcar-leidas/', views.marcar_todas_como_leidas, name='marcar_todas_leidas'),
]
