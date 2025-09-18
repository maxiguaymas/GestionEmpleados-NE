"""
URL configuration for empleadosProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from empleados import views as empleados_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('usuarios.urls')),
    path('empleados/', include('empleados.urls')),
    path('', empleados_views.dashboard, name='home'),
    path('portal/', empleados_views.employee_dashboard, name='employee_dashboard'),
    path('recibos/', include('recibos.urls')),
    path('horarios/', include('horarios.urls')),
    path('sanciones/', include('sanciones.urls')),
    path('incidentes/', include('incidentes.urls')),
    path('asistencia/', include('asistencia.urls')),
    path('notificaciones/', include('notificaciones.urls')),
    path('reportes/', include('reportes.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)