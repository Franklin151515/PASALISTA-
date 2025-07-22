from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class Usuario(AbstractUser):
    es_docente = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class Curso(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    docente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre
class Inscripcion(models.Model):
    estudiante = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('estudiante', 'curso')  # evita inscripciones duplicadas

    def __str__(self):
        return f"{self.estudiante.username} en {self.curso.nombre}"

import uuid

class Sesion(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return f"Sesión {self.fecha} - {self.curso.nombre}"

class Asistencia(models.Model):
    sesion = models.ForeignKey(Sesion, on_delete=models.CASCADE)
    estudiante = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sesion', 'estudiante')

    def __str__(self):
        return f"{self.estudiante.username} asistió a {self.sesion}"

