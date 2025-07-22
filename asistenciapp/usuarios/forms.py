from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario
from .models import Curso

class RegistroForm(UserCreationForm):
    es_docente = forms.BooleanField(label="¿Es docente?", required=False)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'es_docente', 'password1', 'password2']


class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Nombre del curso'}),
            'descripcion': forms.Textarea(attrs={'placeholder': 'Descripción del curso'}),
        }
