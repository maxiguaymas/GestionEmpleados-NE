from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse


# Create your models here.
def validar_mayor_18(value):
    hoy = timezone.now().date()
    edad = hoy.year - value.year - ((hoy.month, hoy.day) < (value.month, value.day))
    if edad < 18:
        raise ValidationError('El empleado debe ser mayor de 18 años.')

# MODELS EMPLEADOS
class Empleado(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='empleado')
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.IntegerField(unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField()
    genero = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')], default='O')
    estado_civil = models.CharField(max_length=20, choices=[('Soltero', 'Soltero'), ('Casado', 'Casado'), ('Divorciado', 'Divorciado'), ('Viudo', 'Viudo')], default='Soltero')
    fecha_nacimiento = models.DateField(validators=[validar_mayor_18])
    estado = models.CharField(max_length=20, choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo'), ('Suspendido', 'Suspendido'), ('Licencia', 'Licencia')], default='Activo')
    ruta_foto = models.ImageField(upload_to='empleados/fotos/', blank=True, null=True)
    fecha_ingreso = models.DateField(auto_now_add=True)
    fecha_egreso = models.DateField(blank=True, null=True)
    


    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.dni}"
    
    def get_iniciales(self):
        # Misma lógica que arriba
        if self.nombre and self.apellido:
            return f"{self.nombre[0]}{self.apellido[0]}".upper()
        elif self.nombre:
            return f"{self.nombre[0]}".upper()
        return ""

    def get_absolute_url(self):
        return reverse('ver_empleado', kwargs={'id': self.id})
    

class RequisitoDocumento(models.Model):
    nombre_doc = models.CharField(max_length=100)
    estado_doc = models.BooleanField(default=True)  # Activo/Inactivo
    obligatorio = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre_doc

class Legajo(models.Model):
    id_empl = models.OneToOneField('Empleado', on_delete=models.CASCADE, related_name='legajo')
    estado_leg = models.CharField(max_length=50)
    fecha_creacion_leg = models.DateField(auto_now_add=True)
    nro_leg = models.IntegerField(unique=True)
    fecha_modificacion_leg = models.DateField(auto_now=True)

class Documento(models.Model):
    id_leg = models.ForeignKey(Legajo, on_delete=models.CASCADE)
    id_requisito = models.ForeignKey(RequisitoDocumento, on_delete=models.CASCADE)
    ruta_archivo = models.FileField(upload_to='legajos/documentos/')
    fecha_hora_subida = models.DateTimeField(auto_now_add=True)
    descripcion_doc = models.CharField(max_length=255, blank=True, null=True)
    estado_doc = models.BooleanField(default=True)

# MODELS DE RECIBOS
class Recibo_Sueldos(models.Model):
    id_empl = models.ForeignKey('Empleado', on_delete=models.CASCADE, related_name='recibos')
    fecha_emision = models.DateField()
    periodo = models.CharField(max_length=7)
    ruta_pdf = models.FileField(upload_to='recibos/pdf/')
    ruta_imagen = models.ImageField(upload_to='recibos/imagenes/', blank=True, null=True)

    def __str__(self):
        return f"Recibo {self.pk} - {self.id_empl.nombre} {self.id_empl.apellido}"
  #Clase horarios debe estar al mismo nivel que Empleado
  
# MODELS DE HORARIOS
class Horarios(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField()
    lunes = models.BooleanField(default=True)
    martes = models.BooleanField(default=True)
    miercoles = models.BooleanField(default=True)
    jueves = models.BooleanField(default=True)
    viernes = models.BooleanField(default=True)
    sabado = models.BooleanField(default=False)
    domingo = models.BooleanField(default=False)
    cantidad_personal_requerida = models.PositiveIntegerField(default=1, verbose_name="Cantidad de Personal Requerida")

    def __str__(self):
        return f"{self.nombre} ({self.hora_entrada.strftime('%H:%M')} - {self.hora_salida.strftime('%H:%M')})"

class AsignacionHorario(models.Model):
    id_empl = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='asignaciones_horario')
    id_horario = models.ForeignKey(Horarios, on_delete=models.CASCADE, related_name='asignaciones')
    fecha_asignacion = models.DateField(auto_now_add=True)
    estado = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Asignación de {self.id_empl.nombre} {self.id_empl.apellido} - {self.id_horario.nombre}"
    
# INCIDENTES
class Incidente(models.Model):
    tipo_incid = models.CharField(max_length=255)
    descripcion_incid= models.CharField(max_length=255)
    estado_incid = models.BooleanField(default=True)

    def __str__(self):
        return self.tipo_incid
    
class Descargo(models.Model):
    fecha_descargo = models.DateField()
    contenido_descargo = models.CharField(max_length=255)
    ruta_archivo_descargo = models.FileField(upload_to='descargos/', blank=True, null=True)
    estado_descargo = models.BooleanField(default=True)

    def __str__(self):
        return f"Descargo {self.pk} para {self.id_incid_empl}"
    
class Resolucion(models.Model):
    fecha_resolucion = models.DateField()
    descripcion = models.CharField(max_length=255)
    responsable = models.CharField(max_length=255)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"Resolucion para sanción ID: {self.sancion_empleado.id}"

class IncidenteEmpleado(models.Model):
    ESTADO_CHOICES = [
        ('ABIERTO', 'Abierto'),
        ('CERRADO', 'Cerrado'),
        ('CORREGIDO', 'Corregido'),
    ]

    id_incidente = models.ForeignKey(Incidente, on_delete=models.CASCADE)
    id_empl = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    id_descargo = models.ForeignKey(Descargo, on_delete=models.SET_NULL, null=True, blank=True)
    id_resolucion = models.ForeignKey(Resolucion, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_ocurrencia = models.DateField()
    observaciones = models.CharField(max_length=255)
    responsable_registro = models.CharField(max_length=255)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='ABIERTO')
    
    # Campo para versionado
    incidente_anterior = models.OneToOneField(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidente_siguiente'
    )

    class Meta:
        unique_together = ('id_incidente', 'id_empl') # Assuming composite key, or just a unique ID for the relationship
                                                    # Based on the ERD, it seems id_incid_empl is the primary key.

    def __str__(self):
        # Corregido para usar tipo_incid que sí existe en el modelo Incidente
        return f"Inc. {self.id_incidente.tipo_incid} - Emp. {self.id_empl.nombre} {self.id_empl.apellido}"




# MODELS DE SANCIONES

class Sancion(models.Model):
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50)
    descripcion = models.TextField()
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class SancionEmpleado(models.Model):
    id_empl = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='sanciones_empleado')
    id_sancion = models.ForeignKey(Sancion, on_delete=models.CASCADE)
    incidente_asociado = models.ForeignKey('IncidenteEmpleado', on_delete=models.SET_NULL, null=True, blank=True, related_name='sanciones')
    fecha_sancion = models.DateField(auto_now_add=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(blank=True, null=True)
    motivo = models.CharField(max_length=255)
    responsable = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Sanción de Empleado"
        verbose_name_plural = "Sanciones de Empleados"

    @property
    def esta_activa(self):
        """
        Determina si la sanción está activa dinámicamente.
        Una sanción está activa si la fecha actual se encuentra
        entre la fecha de inicio y la fecha de fin (inclusive).
        Si no hay fecha_fin, se considera activa indefinidamente
        a partir de la fecha_inicio.
        """
        hoy = timezone.now().date()
        if self.fecha_fin is None:
            return hoy >= self.fecha_inicio
        return self.fecha_inicio <= hoy <= self.fecha_fin

    def __str__(self):
        return f"Sancion {self.id_sancion.nombre} para {self.id_empl.nombre} {self.id_empl.apellido}"

    

# NOTIFICACIONES
class Notificacion(models.Model):
    id_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones', help_text="Empleado que recibirá la notificación.")
    mensaje = models.TextField(help_text="El contenido de la notificación.")
    leida = models.BooleanField(default=False, help_text="Indica si la notificación ha sido leída.")
    fecha_creacion = models.DateTimeField(auto_now_add=True, help_text="Fecha y hora de creación de la notificación.")
    enlace = models.CharField(max_length=255, blank=True, null=True, help_text="URL a la que se redirigirá al hacer clic. Puede ser una URL absoluta o una ruta relativa de Django.")

    def __str__(self):
        """
        Representación en cadena del modelo, útil en el panel de administración.
        """
        return f"Notificación para {self.id_user.username} - Leída: {self.leida}"

    class Meta:
        ordering = ['-fecha_creacion']  # Ordena las notificaciones de más reciente a más antigua.
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        
    

# AUDITORIA
class Auditoria(models.Model):
    """
    Modelo para registrar eventos de auditoría (creación, actualización, eliminación)
    en otras tablas del sistema, vinculando directamente al usuario que realiza la acción.
    """

    class Accion(models.TextChoices):
        """Define las acciones posibles que se pueden auditar."""
        INSERT = 'INSERT', 'Inserción'
        UPDATE = 'UPDATE', 'Actualización'
        DELETE = 'DELETE', 'Eliminación'

    # --- Campos de la tabla ---

    tabla = models.CharField(
        max_length=64,
        help_text="Nombre de la tabla afectada."
    )
    registro_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="Clave primaria (ID) del registro afectado."
    )
    accion = models.CharField(
        max_length=6,
        choices=Accion.choices,
        help_text="Acción realizada sobre el registro (INSERT, UPDATE, DELETE)."
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Vincula al modelo de usuario activo en tu proyecto
        on_delete=models.SET_NULL, # Si se elimina el usuario, el campo actor queda en NULL
        null=True,
        blank=True,
        related_name='acciones_auditoria', # Permite acceder a las auditorías desde un usuario
        help_text="Usuario que realizó la acción."
    )
    datos = models.JSONField(
        null=True,
        blank=True,
        help_text="Datos del registro en formato JSON (ej. estado anterior o posterior)."
    )
    creado_en = models.DateTimeField(
        auto_now_add=True, # Establece la fecha y hora automáticamente al crear el registro
        help_text="Fecha y hora en que se registró el evento."
    )

    # --- Configuración del modelo (Meta) ---

    class Meta:
        db_table = 'auditoria'  # Asegura que el nombre de la tabla en la BD sea 'auditoria'
        ordering = ['-creado_en'] # Ordena los registros por fecha descendente por defecto
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'

    # --- Representación en texto del objeto ---

    def __str__(self):
        """
        Devuelve una representación legible del objeto en el admin de Django
        y en otras partes del sistema.
        """
        actor_info = self.actor.username if self.actor else "Sistema"
        return f'{self.accion} en {self.tabla} (ID: {self.pk}) por {actor_info}'