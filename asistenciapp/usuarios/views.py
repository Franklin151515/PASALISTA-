# IMPORTACIONES
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from .forms import RegistroForm, CursoForm
from .models import Curso, Inscripcion, Sesion, Asistencia

import qrcode
import io
import base64

# VISTAS DE AUTENTICACIÓN
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

# VISTA PRINCIPAL SEGÚN ROL
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

# CREACIÓN DE CURSOS (DOCENTE)
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

# INSCRIPCIÓN A CURSOS (ESTUDIANTE)
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

# CREAR SESIÓN (DOCENTE)
@login_required
def crear_sesion_view(request, curso_id):
    if not request.user.es_docente:
        return HttpResponseForbidden("Solo docentes pueden crear sesiones.")

    curso = Curso.objects.get(id=curso_id)

    if curso.docente != request.user:
        return HttpResponseForbidden("No tienes permiso para este curso.")

    sesion = Sesion.objects.create(curso=curso)
    return redirect('ver_qr', sesion_id=sesion.id)

# GENERAR QR
@login_required
def ver_qr_view(request, sesion_id):
    sesion = Sesion.objects.get(id=sesion_id)

    # Cambia 'localhost' por la IP local de tu PC
    ip_local = "192.168.31.46"  # Cambia esto por la IP de tu PC en la red
    url_asistencia = f'http://{ip_local}:8000/asistencia/{sesion.uuid}/'

    qr = qrcode.make(url_asistencia)
    buffer = io.BytesIO()
    qr.save(buffer, format='PNG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render(request, 'usuarios/ver_qr.html', {
        'sesion': sesion,
        'qr_base64': img_base64,
        'url_asistencia': url_asistencia
    })

# REGISTRAR ASISTENCIA
@login_required
def registrar_asistencia_view(request, uuid):
    try:
        sesion = Sesion.objects.get(uuid=uuid)
    except Sesion.DoesNotExist:
        return HttpResponse("Sesión no encontrada.", status=404)

    if request.user.es_docente:
        return HttpResponse("Los docentes no registran asistencia.", status=403)

    if not Inscripcion.objects.filter(estudiante=request.user, curso=sesion.curso).exists():
        return HttpResponse("No estás inscrito en este curso.", status=403)

    if Asistencia.objects.filter(sesion=sesion, estudiante=request.user).exists():
        return HttpResponse("Ya registraste tu asistencia para esta sesión.", status=400)

    Asistencia.objects.create(sesion=sesion, estudiante=request.user)
    return HttpResponse("✅ Asistencia registrada exitosamente.")

# VER ASISTENTES (DOCENTE)
@login_required
def ver_asistentes_view(request, sesion_id):
    sesion = get_object_or_404(Sesion, id=sesion_id)

    if not request.user.es_docente or sesion.curso.docente != request.user:
        return HttpResponse("No tienes permiso para ver esta sesión.", status=403)

    asistentes = Asistencia.objects.filter(sesion=sesion).select_related('estudiante')

    return render(request, 'usuarios/ver_asistentes.html', {
        'sesion': sesion,
        'asistentes': asistentes
    })

# HISTORIAL DE ASISTENCIA (ESTUDIANTE)
@login_required
def historial_estudiante_view(request):
    asistencias = Asistencia.objects.filter(estudiante=request.user).select_related('sesion__curso').order_by('-sesion__fecha')
    return render(request, 'usuarios/historial_estudiante.html', {
        'asistencias': asistencias
    })

# HISTORIAL DE SESIONES Y ASISTENCIA (DOCENTE)
@login_required
def historial_docente_view(request):
    if not request.user.es_docente:
        return redirect('inicio')

    cursos = Curso.objects.filter(docente=request.user)
    data = []

    for curso in cursos:
        sesiones = Sesion.objects.filter(curso=curso).order_by('-fecha')
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

    return render(request, 'usuarios/historial_docente.html', {
        'historial': data
    })

# CÁMARA PARA ESCANEAR QR
@login_required
def camaraqr_view(request):
    return render(request, 'usuarios/camaraqr.html')
