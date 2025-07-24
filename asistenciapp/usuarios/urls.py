from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio_view, name='inicio'),
    path('registro/', views.registro_view, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('inicio/', views.inicio_view, name='inicio'),
    path('crear-curso/', views.crear_curso_view, name='crear_curso'),
    path('cursos-disponibles/', views.cursos_disponibles_view, name='cursos_disponibles'),
    path('mis-cursos/', views.mis_cursos_view, name='mis_cursos'),
    path('curso/<int:curso_id>/crear-sesion/', views.crear_sesion_view, name='crear_sesion'),
    path('sesion/<int:sesion_id>/ver-qr/', views.ver_qr_view, name='ver_qr'),
    path('asistencia/<uuid:uuid>/', views.registrar_asistencia_view, name='registrar_asistencia'),
    path('ver-asistentes/<int:sesion_id>/', views.ver_asistentes_view, name='ver_asistentes'),
    path('historial-estudiantes/', views.historial_estudiante_view, name='historial_estudiante'),
    path('historial-docentes/', views.historial_docente_view, name='historial_docente'),
    path('camaraqr/', views.camaraqr_view, name='camaraqr'),
]
