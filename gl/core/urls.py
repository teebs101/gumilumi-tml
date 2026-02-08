from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    # --- ADMIN & AUTH ---
    path("admin/", admin.site.urls),
    path('', views.landing_view, name='landing'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # --- PANEL PRINCIPAL ---
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logros/', views.logros_view, name='logros'),
    path('chat/', views.chat_view, name='chat'),
    path('account/', views.account_view, name='account'),
    path('update_profile/', views.update_profile, name='update_profile'),

    # --- CURSOS Y LECCIONES ---
    path("courses/", views.courses_view, name="courses"),
    path("course/<int:course_id>/", views.course_detail_view, name="course_detail"),
    
    # Explicación (Teoría)
    path('lesson/<int:lesson_id>/', views.lesson_explanation_view, name='lesson_explanation'),
    
    path('terminal/mision/<int:lesson_id>/', views.lesson_terminal_view, name='lesson_terminal'),
    path('terminal/practica/', views.terminal_practica_view, name='terminal_practica'), # Nueva ruta para modo libre
     path('terminal_libre/', views.terminal_libre_view, name='terminal_libre'),

    # Ejecución (AJAX)
    path('ejecutar-codigo/', views.ejecutar_codigo_view, name='ejecutar_codigo'),
   path('lesson/complete/<int:lesson_id>/', views.completar_leccion_terminal, name='completar_leccion_terminal'),

    # --- RETOS Y MISIONES ---
    path('complete-mission/', views.complete_mission, name='complete_mission'),
    path('retos/', views.retos_view, name='retos'),
    # Aquí cambiamos 'hacer_reto_view' por 'validar_reto'
    path('validar-reto/<int:reto_id>/', views.validar_reto, name='validar_reto'),

    # --- PÁGINAS INFORMATIVAS ---
    path('enproceso/', views.enproceso_view, name='en_proceso'),
    path('terminos/', views.terminos_view, name='terminos'),
    path('soporte/', views.soporte_view, name='soporte'),
    path('desarrolladores/', views.desarrolladores_view, name='desarrolladores'),
    path('sobrenos/', views.sobrenos_view, name='sobrenosotros'),
    path('queaprender/', views.que_aprender_view, name='queaprender'),
    path('feedback/', views.enviar_feedback, name='feedback_page'),

    path("api/chat/", views.chat_api, name="chat_api"),
]


