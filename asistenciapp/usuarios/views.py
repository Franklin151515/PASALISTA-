from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import RegistroForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import CursoForm
from .models import Inscripcion
from django.shortcuts import get_object_or_404
from django.http import HttpResponse


def registro_view(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistroForm()
    return render(request, 'usuarios/registro.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('inicio')
        else:
            return render(request, 'usuarios/login.html', {'error': 'Credenciales inválidas'})
    return render(request, 'usuarios/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

from .models import Curso

@login_required
def inicio_view(request):
    usuario = request.user
    cursos = []

    if usuario.es_docente:
        cursos = Curso.objects.filter(docente=usuario)

    return render(request, 'usuarios/inicio.html', {
        'usuario': usuario,
        'cursos': cursos
    })


@login_required
def crear_curso_view(request):
    if not request.user.es_docente:
        return HttpResponseForbidden("Solo los docentes pueden crear cursos.")

    if request.method == 'POST':
        form = CursoForm(request.POST)
        if form.is_valid():
            curso = form.save(commit=False)
            curso.docente = request.user
            curso.save()
            return redirect('inicio')
    else:
        form = CursoForm()

    return render(request, 'usuarios/crear_curso.html', {'form': form})

@login_required
def cursos_disponibles_view(request):
    if request.user.es_docente:
        return HttpResponseForbidden("Solo los estudiantes pueden inscribirse.")

    cursos = Curso.objects.exclude(inscripcion__estudiante=request.user)

    if request.method == 'POST':
        curso_id = request.POST.get('curso_id')
        curso = Curso.objects.get(id=curso_id)
        Inscripcion.objects.create(estudiante=request.user, curso=curso)
        return redirect('mis_cursos')

    return render(request, 'usuarios/cursos_disponibles.html', {'cursos': cursos})

@login_required
def mis_cursos_view(request):
    if request.user.es_docente:
        return HttpResponseForbidden("Solo los estudiantes pueden ver esta vista.")

    inscripciones = Inscripcion.objects.filter(estudiante=request.user)
    return render(request, 'usuarios/mis_cursos.html', {'inscripciones': inscripciones})

from .models import Sesion

@login_required
def crear_sesion_view(request, curso_id):
    if not request.user.es_docente:
        return HttpResponseForbidden("Solo docentes pueden crear sesiones.")

    curso = Curso.objects.get(id=curso_id)

    if curso.docente != request.user:
        return HttpResponseForbidden("No tienes permiso para este curso.")

    sesion = Sesion.objects.create(curso=curso)
    return redirect('ver_qr', sesion_id=sesion.id)

import qrcode
import io
import base64

@login_required
def ver_qr_view(request, sesion_id):
    sesion = Sesion.objects.get(id=sesion_id)

    if sesion.curso.docente != request.user:
        return HttpResponseForbidden("No puedes ver este QR.")

    url_asistencia = request.build_absolute_uri(f'/asistencia/{sesion.uuid}/')

    qr = qrcode.make(url_asistencia)
    buffer = io.BytesIO()
    qr.save(buffer, format='PNG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render(request, 'usuarios/ver_qr.html', {
        'sesion': sesion,
        'qr_base64': img_base64,
        'url_asistencia': url_asistencia
    })

from .models import Asistencia

@login_required
def registrar_asistencia_view(request, uuid):
    try:
        sesion = Sesion.objects.get(uuid=uuid)
    except Sesion.DoesNotExist:
        return HttpResponse("Sesión no encontrada.", status=404)

    # Verificar que el usuario sea estudiante
    if request.user.es_docente:
        return HttpResponse("Los docentes no registran asistencia.", status=403)

    # Verificar que el estudiante esté inscrito en el curso
    if not Inscripcion.objects.filter(estudiante=request.user, curso=sesion.curso).exists():
        return HttpResponse("No estás inscrito en este curso.", status=403)

    # Verificar si ya registró asistencia
    if Asistencia.objects.filter(sesion=sesion, estudiante=request.user).exists():
        return HttpResponse("Ya registraste tu asistencia para esta sesión.", status=400)

    # Registrar asistencia
    Asistencia.objects.create(sesion=sesion, estudiante=request.user)
    return HttpResponse("✅ Asistencia registrada exitosamente.")

@login_required
def ver_asistentes_view(request, sesion_id):
    sesion = get_object_or_404(Sesion, id=sesion_id)

    # Asegurar que el usuario sea docente y dueño del curso
    if not request.user.es_docente or sesion.curso.docente != request.user:
        return HttpResponse("No tienes permiso para ver esta sesión.", status=403)

    asistentes = Asistencia.objects.filter(sesion=sesion).select_related('estudiante')

    return render(request, 'usuarios/ver_asistentes.html', {
        'sesion': sesion,
        'asistentes': asistentes
    })
from django.contrib.auth.decorators import login_required
from .models import Asistencia

@login_required
def historial_estudiante_view(request):
    asistencias = Asistencia.objects.filter(estudiante=request.user).select_related('sesion__curso').order_by('-sesion__fecha')
    return render(request, 'usuarios/historial_estudiante.html', {
        'asistencias': asistencias
    })
from django.shortcuts import render
from .models import Curso, Sesion, Asistencia

@login_required
def historial_docente_view(request):
    if not request.user.es_docente:
        return redirect('inicio')

    cursos = Curso.objects.filter(docente=request.user)
    data = []

    for curso in cursos:
        sesiones = Sesion.objects.filter(curso=curso).order_by('-fecha_hora')
        sesiones_data = []

        for sesion in sesiones:
            asistentes = Asistencia.objects.filter(sesion=sesion)
            sesiones_data.append({
                'sesion': sesion,
                'asistentes': asistentes
            })

        data.append({
            'curso': curso,
            'sesiones': sesiones_data
        })

    return render(request, 'usuarios/historial_asistencia.html', {
        'historial': data
    })
