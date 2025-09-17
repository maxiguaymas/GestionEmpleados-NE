from django.db import models
from empleados.models import Empleado # Asegúrate que la importación sea correcta
import json

class Rostro(models.Model):
    id_empl = models.OneToOneField(Empleado, on_delete=models.CASCADE, primary_key=True)
    encoding = models.TextField() # Almacenaremos el encoding facial como un string JSON

    def set_encoding(self, encoding_array):
        self.encoding = json.dumps(encoding_array.tolist())

    def get_encoding(self):
        return json.loads(self.encoding)

    def __str__(self):
        return f"Rostro de {self.id_empl.nombre} {self.id_empl.apellido}"

class Asistencia(models.Model):
    id_empl = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    minutos_retraso= models.IntegerField(default=0)
    # Podrías agregar un campo 'tipo' si quieres diferenciar entre 'Entrada' y 'Salida'

    def __str__(self):
        return f"Asistencia de {self.id_empl.nombre} - {self.fecha_hora.strftime('%Y-%m-%d %H:%M')}"