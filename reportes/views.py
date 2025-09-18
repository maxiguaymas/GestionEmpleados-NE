from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from .forms import ReporteAsistenciaForm
from asistencia.models import Asistencia
from empleados.models import Empleado
import pandas as pd
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from datetime import datetime, timedelta

class GenerarReporteAsistencia(View):
    def get(self, request, *args, **kwargs):
        form = ReporteAsistenciaForm()
        return render(request, 'reportes/generar_reporte.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = ReporteAsistenciaForm(request.POST)
        if form.is_valid():
            tipo_reporte = form.cleaned_data['tipo_reporte']
            hoy = datetime.now()

            if tipo_reporte == 'semanal':
                start_date = hoy - timedelta(days=hoy.weekday())
                end_date = start_date + timedelta(days=6)
            elif tipo_reporte == 'mensual':
                start_date = hoy.replace(day=1)
                next_month = hoy.replace(day=28) + timedelta(days=4) # a safe way to get to the next month
                end_date = next_month - timedelta(days=next_month.day)
            else: # anual
                start_date = hoy.replace(month=1, day=1)
                end_date = hoy.replace(month=12, day=31)

            asistencias = Asistencia.objects.filter(fecha_hora__range=[start_date, end_date])
            if not asistencias.exists():
                return HttpResponse("No hay datos de asistencia para el período seleccionado.")

            data = {
                'Empleado': [f'{a.id_empl.nombre} {a.id_empl.apellido}' for a in asistencias],
                'Fecha y Hora': [a.fecha_hora.strftime('%Y-%m-%d %H:%M:%S') for a in asistencias],
                'Minutos de Retraso': [a.minutos_retraso for a in asistencias],
            }
            df = pd.DataFrame(data)

            template = get_template('reportes/reporte_template.html')
            context = {
                'report_title': f'Reporte de Asistencia {tipo_reporte.capitalize()}',
                'df_html': df.to_html(classes='table table-striped', index=False)
            }
            html = template.render(context)

            result = BytesIO()
            pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
            if not pdf.err:
                return HttpResponse(result.getvalue(), content_type='application/pdf')
        return HttpResponse("Error al generar el PDF", status=400)