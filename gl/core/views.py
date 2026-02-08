# ===============================
# IMPORTS GENERALES
# ===============================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from .models import Feedback
from django.contrib import messages
import random
from django.shortcuts import render
from .models import Reto, RetoCompletado

# Tus modelos
from .models import (
    Course, Lesson, Profile, UserLessonProgress,
    Achievement, UserAchievement, Mission, UserMission,
    Reto, RetoCompletado
)

from .models import UserLessonProgress, Lesson

def global_context(request):
    if request.user.is_authenticated:
        # Reutilizamos tu lógica del views.py
        ultimo = UserLessonProgress.objects.filter(user=request.user, completed=True).order_by('-completed_at').first()
        if ultimo:
            proxima = Lesson.objects.filter(course=ultimo.lesson.course, order__gt=ultimo.lesson.order).first()
        else:
            proxima = Lesson.objects.order_by('course__id', 'order').first()
        
        return {'proxima_leccion': proxima}
    return {}


# ===============================
# LANDING & AUTHENTICATION
# ===============================

def landing_view(request):
    comentarios = Feedback.objects.all().order_by('-fecha')[:6] # Trae los últimos 6
    return render(request, 'core/landing.html', {'comentarios': comentarios})

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name', '') # Nuevo: Nombre real
        last_name = request.POST.get('last_name', '')   # Nuevo: Apellido
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')           # Nuevo: Teléfono
        password = request.POST.get('password')
        avatar_choice = request.POST.get('avatar', 'gumi')

        if User.objects.filter(username=username).exists():
            return render(request, 'core/register.html', {'error': '¡Ese apodo ya está en uso!'})

        # Creamos el usuario con sus datos reales
        user = User.objects.create_user(
            username=username, 
            email=email, 
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Actualizamos el perfil con los datos extra
        perfil = user.profile
        perfil.avatar = avatar_choice
        perfil.nickname = username
        perfil.phone = phone
        perfil.save()

        # Logro de bienvenida
        logro = Achievement.objects.filter(name="Primeros Pasos").first()
        if logro:
            UserAchievement.objects.get_or_create(user=user, achievement=logro)

        login(request, user)
        return redirect('dashboard')
    return render(request, 'core/register.html')

def login_view(request):
    if request.method == "POST":
        user = authenticate(username=request.POST.get("username"), password=request.POST.get("password"))
        if user:
            login(request, user)
            return redirect("dashboard")
        messages.error(request, "Usuario o contraseña incorrectos 😿")
    return render(request, "core/login.html")

def logout_view(request):
    logout(request)
    return redirect("landing")

# ===============================
# DASHBOARD & MISIONES
# ===============================

@login_required
def dashboard_view(request):
    perfil = request.user.profile # Acceso rápido al perfil
    
    # 1. Lógica de Próxima Lección
    ultimo = UserLessonProgress.objects.filter(user=request.user, completed=True).order_by('-completed_at').first()
    if ultimo:
        proxima = Lesson.objects.filter(course=ultimo.lesson.course, order__gt=ultimo.lesson.order).first()
        if not proxima: 
            proxima = Lesson.objects.filter(course__id__gt=ultimo.lesson.course.id).order_by('course__id', 'order').first()
    else:
        proxima = Lesson.objects.order_by('course__id', 'order').first()

    # 2. Lógica de Retos
    completados = RetoCompletado.objects.filter(user=request.user).values_list('reto_id', flat=True)
    retos_disponibles = Reto.objects.filter(esta_activo=True).exclude(id__in=completados)
    
    reto_aleatorio = None
    if retos_disponibles.exists():
        reto_aleatorio = random.choice(retos_disponibles)
    
    # 3. Datos de Rango para la UI
    rango = perfil.rango # Usamos la propiedad que creamos en models.py

    return render(request, 'core/dashboard.html', {
        'proxima_leccion': proxima,
        'reto_rapido': reto_aleatorio,
        'rango': rango, # <-- Pasamos el dict con color, icono y nombre
        'perfil': perfil
    })

@login_required
def complete_mission(request):
    if request.method == "POST":
        mission_id = request.POST.get('mission_id')
        mission = get_object_or_404(Mission, id=mission_id)
        profile = request.user.profile
        user_mission, created = UserMission.objects.get_or_create(user=request.user, mission=mission)

        if not user_mission.completed:
            user_mission.completed = True
            user_mission.save()
            profile.xp += mission.xp_reward
            profile.level = (profile.xp // 100) + 1
            profile.save()
            return JsonResponse({'status': 'success', 'xp_ganado': mission.xp_reward, 'nivel_actual': profile.level})
    return JsonResponse({'status': 'error'}, status=400)

# ===============================
# CURSOS Y LECCIONES
# ===============================

@login_required
def courses_view(request):
    categoria = request.GET.get('cat', 'all')
    courses = Course.objects.all() if categoria == 'all' else Course.objects.filter(category=categoria)
    return render(request, 'core/cursos.html', {'courses': courses, 'categoria_activa': categoria})

@login_required
def course_detail_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    perfil = request.user.profile

    requisitos_nivel = {
        1: 1,  # Intro
        2: 3,  # Variables
        3: 6,  # Condicionales
        4: 10, # Bucles
    }

    nivel_necesario = requisitos_nivel.get(course.id, 1) # Por defecto nivel 1

    if perfil.level < nivel_necesario:
        messages.warning(request, f"¡Alto ahí, explorador! Necesitas ser Nivel {nivel_necesario} para entrar al {course.title}. 🔒")
        return redirect('courses') # O a una página de 'nivel insuficiente'

    # Inscripción automática
    if course not in perfil.cursos_inscritos.all():
        perfil.cursos_inscritos.add(course)

    lecciones = course.lessons.all().order_by('order')
    
    # --- LÓGICA DE LOGROS DEL REINO ---
    # 1. Traemos los 3 logros de este curso (asegúrate de crearlos en el Admin con order 1, 2 y 3)
    logros_reino = Achievement.objects.filter(curso=course).order_by('order')
    
    # 2. Obtenemos los IDs de los que el usuario ya ganó
    logros_ganados_ids = UserAchievement.objects.filter(
        user=request.user, 
        achievement__curso=course
    ).values_list('achievement_id', flat=True)

    # --- PROGRESO ---
    completadas = UserLessonProgress.objects.filter(
        user=request.user, 
        lesson__course=course, 
        completed=True
    ).values_list('lesson_id', flat=True)

    total = lecciones.count()
    hechas = completadas.count()
    porcentaje = int((hechas / total) * 100) if total > 0 else 0

    return render(request, 'core/curso_detalle.html', {
        'course': course, 
        'lecciones': lecciones, 
        'completadas': completadas,
        'progreso': porcentaje,
        'logros_reino': logros_reino,         # <-- Nuevo
        'logros_ganados_ids': logros_ganados_ids # <-- Nuevo
    })

@login_required
def lesson_explanation_view(request, lesson_id):
    leccion = get_object_or_404(Lesson, id=lesson_id)
    course = leccion.course
    
    # Cálculo de progreso para la barra lateral
    total_lessons = course.lessons.count()
    completed_count = UserLessonProgress.objects.filter(user=request.user, lesson__course=course, completed=True).count()
    progress_percentage = int((completed_count / total_lessons) * 100) if total_lessons > 0 else 0

    return render(request, 'core/leccion.html', {
        'lesson': leccion,
        'progress_percentage': progress_percentage,
        'completed_count': completed_count,
        'total_lessons': total_lessons,
    })

# ===============================
# TERMINAL Y EJECUCIÓN
# ===============================

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Lesson, UserLessonProgress

@login_required
def lesson_terminal_view(request, lesson_id):
    # 1. Obtenemos la lección actual
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    # 2. Lógica de Seguridad (Opcional pero Recomendada)
    # Verificamos si el usuario completó la lección anterior antes de entrar a esta
    leccion_anterior = Lesson.objects.filter(
        course=lesson.course, 
        order__lt=lesson.order
    ).order_by('-order').first()

    if leccion_anterior:
        progreso_anterior = UserLessonProgress.objects.filter(
            user=request.user, 
            lesson=leccion_anterior, 
            completed=True
        ).exists()
        
        if not progreso_anterior:
            messages.warning(request, "⚠️ Acceso denegado: Debes descifrar la misión anterior primero.")
            return redirect('dashboard')

    # 3. Verificar estado de la lección actual
    # Esto sirve para mostrar en la UI si ya está "Hackeada"
    progreso_actual = UserLessonProgress.objects.filter(
        user=request.user, 
        lesson=lesson
    ).first()
    
    ya_completada = progreso_actual.completed if progreso_actual else False

    # 4. Contexto Pro
    # Si no tienes 'objetivo_1' en el modelo, podemos simular objetivos
    # separando el contenido por puntos si usas algún caracter especial, 
    # o simplemente pasando el contenido limpio.
    context = {
        'lesson': lesson,
        'ya_completada': ya_completada,
        'xp_recompensa': lesson.xp_leccion if hasattr(lesson, 'xp_leccion') else 100,
        'modulo_nombre': lesson.course.title if lesson.course else "Misión Independiente",
    }

    return render(request, 'core/terminal_leccion.html', context)

# core/views.py
from django.shortcuts import render, get_object_or_404
from .models import Reto

@login_required
def terminal_practica_view(request):
    # 1. Atrapamos el ID de la URL
    reto_id = request.GET.get('reto_id')
    reto = None

    # 2. Si hay ID, buscamos el reto
    if reto_id:
        try:
            reto = Reto.objects.get(id=int(reto_id))
            print(f"✅ Reto {reto_id} cargado con éxito")
        except:
            reto = None
            print(f"❌ No se encontró el reto con ID {reto_id}")

    # 3. Mandamos TODO al HTML
    return render(request, 'core/terminal_practica.html', {
        'reto': reto,
        'debug_id': reto_id,
        'modo_libre': False if reto else True
    })

import sys
import io
import traceback
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Lesson # Asegúrate de que el import sea correcto

def ejecutar_codigo_view(request):
    if request.method == "POST":
        code = request.POST.get('code', '')
        lesson_id = request.POST.get('lesson_id')
        
        output_buffer = io.StringIO()
        error_line = None
        status = "error"
        output = ""
        
        try:
            # 1. Redirigir salida
            sys.stdout = output_buffer
            
            # Ejecutamos el código
            # Nota: Usamos locals y globals para que las funciones y variables funcionen mejor
            exec_scope = {}
            exec(code, exec_scope, exec_scope) 
            
            output = output_buffer.getvalue()
            status = "success"
            
            # 2. Validar meta (solo si el código corrió sin errores)
            try:
                lesson = Lesson.objects.get(id=lesson_id)
                meta = lesson.codigo_meta.lower().strip()
                
                if meta in code.lower():
                    output += f"\n\n✨ [SISTEMA DESBLOQUEADO] ✨\n🚩 FLAG: {lesson.flag_secreta}"
                else:
                    output += f"\n\n🐻 Gumi dice: El hechizo funcionó, pero te falta usar '{meta}' para revelar la flag."
            except Lesson.DoesNotExist:
                pass

        except Exception as e:
            # CAPTURAMOS LO QUE SE ALCANZÓ A IMPRIMIR ANTES DEL ERROR
            output_previo = output_buffer.getvalue()
            
            # Capturar info del error
            cl, exc, tb = sys.exc_info()
            lineas = traceback.extract_tb(tb)
            if lineas:
                # Si el error es dentro del exec, la línea suele estar en la última posición
                error_line = lineas[-1].lineno
            
            # Mostramos lo que imprimió + el error en rojo (desde el JS)
            output = f"{output_previo}\n❌ ERROR EN TU CÓDIGO:\n{str(e)}"
            status = "fail" # Cambiamos a fail para que el JS sepa que no hubo éxito
            
        finally:
            # SIEMPRE devolvemos la salida al sistema
            sys.stdout = sys.__stdout__

        return JsonResponse({
            'output': output,
            'error_line': error_line,
            'status': status
        })
    
@login_required
def completar_leccion_terminal(request, lesson_id):
    if request.method == "POST":
        import json
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Datos inválidos'}, status=400)
        
        uso_pista = data.get('uso_pista', False)
        flag_user = data.get('flag', '').strip()
        lesson = get_object_or_404(Lesson, id=lesson_id)
        perfil = request.user.profile 

        # 1. Validación de la bandera
        if flag_user != lesson.flag_secreta:
            return JsonResponse({'status': 'error', 'message': '¡Esa no es la bandera! Sigue intentando 🧙‍♂️'}, status=400)

        progreso, created = UserLessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
        logro_ganado_data = None
        xp_final_ganada = 0

        # 2. Solo procesamos si es la primera vez que completa esta lección
        if not progreso.completed:
            xp_base = lesson.xp_leccion 
            xp_final_ganada = max(0, xp_base - 5 if uso_pista else xp_base)

            progreso.completed = True
            progreso.save()
            perfil.add_xp(xp_final_ganada) 
            
            # --- LÓGICA DE LOGROS AUTOMÁTICOS ---
            course = lesson.course
            lecciones_total = course.lessons.count()
            lecciones_hechas = UserLessonProgress.objects.filter(
                user=request.user, lesson__course=course, completed=True
            ).count()

            logro_a_otorgar = None
            mensaje_custom = ""

            # Logro 1: El despertar (Primera lección)
            if lecciones_hechas == 1:
                logro_a_otorgar = Achievement.objects.filter(curso=course, order=1).first()
                mensaje_custom = "¡Tu primera victoria en este reino!"
            
            # Logro 2: El camino medio (Evitamos que coincida con la lección 1)
            elif lecciones_hechas == (lecciones_total // 2) and lecciones_hechas > 1:
                logro_a_otorgar = Achievement.objects.filter(curso=course, order=2).first()
                mensaje_custom = "¡Ya estás a mitad de camino, no te detengas!"

            # Logro 3: Conquistador total
            elif lecciones_hechas == lecciones_total:
                logro_a_otorgar = Achievement.objects.filter(curso=course, order=3).first()
                mensaje_custom = "¡Has dominado este reino por completo! Eres una leyenda."

            if logro_a_otorgar:
                ua, created_ua = UserAchievement.objects.get_or_create(
                    user=request.user, 
                    achievement=logro_a_otorgar
                )
                if created_ua:
                    logro_ganado_data = {
                        'nombre': logro_a_otorgar.name,
                        'icono': logro_a_otorgar.icon_name,
                        'mensaje': mensaje_custom,
                        'desc': logro_a_otorgar.description
                    }

        return JsonResponse({
            'status': 'success',
            'xp_ganado': xp_final_ganada,
            'xp_total': perfil.xp,
            'nivel': perfil.level,
            'logro': logro_ganado_data
        })
    
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)



# ===============================
# RETOS MÁGICOS (Quiz, Pregunta, Terminal)
# ===============================

from django.http import JsonResponse
import json

@login_required
def validar_flag(request, lesson_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_flag = data.get('flag', '').strip()
            lesson = get_object_or_404(Lesson, id=lesson_id)
            perfil = request.user.profile

            # Comparamos en el servidor (Seguro)
            if user_flag == lesson.flag_secreta:
                # Evitar que gane XP dos veces por la misma lección
                progreso, created = UserLessonProgress.objects.get_or_create(
                    user=request.user, 
                    lesson=lesson
                )
                
                if not progreso.completed:
                    progreso.completed = True
                    progreso.save()
                    perfil.add_xp(lesson.xp_leccion)
                    
                    return JsonResponse({
                        'status': 'success', 
                        'message': '¡Código descifrado!',
                        'xp_ganada': lesson.xp_leccion
                    })
                else:
                    return JsonResponse({'status': 'info', 'message': 'Ya habías completado esta misión.'})
            
            return JsonResponse({'status': 'error', 'message': 'Frecuencia incorrecta... Inténtalo de nuevo.'}, status=400)
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def retos_view(request):
    # Ahora que ya migraste, 'esta_activo' ya no dará error
    todos_los_retos = Reto.objects.filter(esta_activo=True)
    hechos_ids = RetoCompletado.objects.filter(user=request.user).values_list('reto_id', flat=True)
    
    return render(request, 'core/retos.html', {
        'retos': todos_los_retos,
        'completadas_ids': hechos_ids
    })

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Reto, RetoCompletado # Asegúrate de importar ambos

def validar_reto(request, reto_id):
    reto = get_object_or_404(Reto, id=reto_id)
    respuesta_usuario = request.GET.get('respuesta', '').strip()
    correcta = reto.opciones_o_respuesta.strip()
    
    # --- NUEVA LÓGICA DE SENSIBILIDAD ---
    if not reto.es_case_sensitive:
        es_valido = respuesta_usuario.lower() == correcta.lower()
    else:
        es_valido = respuesta_usuario == correcta

    if es_valido:
        completado, creado = RetoCompletado.objects.get_or_create(
            user=request.user, 
            reto=reto
        )

        xp_a_mostrar = 0
        if creado:
            # Usamos tu método add_xp que ya tienes en el perfil
            request.user.profile.add_xp(reto.xp_recompensa)
            xp_a_mostrar = reto.xp_recompensa
            mensaje = '¡Increíble! Has descifrado el código secreto.'
        else:
            mensaje = '¡Ya habías superado este reto, pero tu magia sigue intacta!'

        return JsonResponse({
            'status': 'success',
            'message': mensaje,
            'xp_ganado': xp_a_mostrar
        })
    
    else:
        return JsonResponse({
            'status': 'error',
            'message': 'Ese no es el código correcto... Gumi dice que revises bien. 🐻'
        })
    
# ===============================
# LOGROS Y CUENTA
# ===============================

@login_required
def logros_view(request):
    # 1. Obtener los que el usuario YA tiene
    ganados = UserAchievement.objects.filter(user=request.user).select_related('achievement')
    ids_ganados = ganados.values_list('achievement_id', flat=True)
    
    # 2. Obtener los que faltan (excluyendo los ganados)
    bloqueados = Achievement.objects.exclude(id__in=ids_ganados)
    
    context = {
        'user_achievements': ganados,
        'locked_achievements': bloqueados,
        'total_achievements_count': Achievement.objects.count()
    }
    return render(request, 'core/logros.html', context)

def otorgar_logro(request, user, nombre):
    logro = Achievement.objects.filter(name=nombre).first()
    if logro:
        obj, created = UserAchievement.objects.get_or_create(user=user, achievement=logro)
        if created:
            messages.success(request, f"¡Desbloqueaste: {nombre}!", extra_tags="logro_ganado")

@login_required
def account_view(request):
    return render(request, 'core/cuenta.html')

@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        email = request.POST.get('email')
        try:
            validate_email(email)
            user.email = email
            user.save()
            return JsonResponse({'status': 'ok'})
        except:
            return JsonResponse({'status': 'error'})
    return JsonResponse({'status': 'error'}, status=405)

def enviar_feedback(request):
    if request.method == 'POST':
        texto = request.POST.get('comentario')
        # Si quieres guardar el sentimiento que seleccionó el niño:
        sentimiento = request.POST.get('feeling', '😊') 
        
        if texto:
            Feedback.objects.create(
                usuario=request.user, 
                mensaje=f"{texto} {sentimiento}"
            )
            
            perfil = request.user.profile
            perfil.add_xp(10) # Usamos el método limpio
            
            messages.success(request, "¡Gumi recibió tu mensaje! +10 XP mágicos. 🌟")
            return redirect('feedback_page') 

    comentarios = Feedback.objects.all().order_by('-fecha')[:10]
    return render(request, 'core/comentarios.html', {'comentarios': comentarios})

# ===============================
# VISTAS INFORMATIVAS
# ===============================
def chat_view(request): return render(request, 'core/chat.html')
def terminal_libre_view(request): return render(request, 'core/terminal_libre.html')
def enproceso_view(request): return render(request, 'core/en_proceso.html')
def que_aprender_view(request): return render(request, 'core/infoaprender.html')
def sobrenos_view(request): return render(request, 'core/sobrenosotros.html')
def terminos_view(request): return render(request, 'core/terminos.html')
def soporte_view(request): return render(request, 'core/soporte.html')
def desarrolladores_view(request): return render(request, 'core/desarrolladores.html')

import os
import requests
import json
from django.http import JsonResponse
from dotenv import load_dotenv

# 1. Cargamos las variables del .env
load_dotenv()

SYSTEM_PROMPT = """
Eres la guía del Reino de Cristal. El mundo se divide en 6 Reinos Mágicos:
1. EL VALLE DE LOS NOMBRES: Donde nacen las Variables (el origen de todo).
2. PANTANO DE LAS DECISIONES: El reino de los Condicionales (If/Else) donde eliges tu camino.
3. CUEVA DE LOS ECOS: Donde viven los Bucles (Loops) y las cosas se repiten mágicamente.
4. BOSQUE DE PERGAMINOS: El lugar de las Listas y diccionarios donde guardamos sabiduría.
5. FORJA DE POCIONES: Donde creamos Funciones (recetas mágicas reutilizables).
6. CASTILLO DE DESAFÍOS: La prueba final de Programación Orientada a Objetos y proyectos.

TUS PERSONAJES:
- LUMI (Coneja 🐰): Dulce, usa emojis (✨, 🚩) y entrega 'Banderas de Código' al superar un reino.
- GUMI (Oso 🐻): Sabio y paciente, ayuda cuando el código falla en la Forja o el Pantano.

REGLAS:
- Si el usuario está perdido, dile en qué Reino se encuentra según el tema.
- Usa frases como: '¡Bienvenida al Valle de los Nombres! Vamos a crear tu primera variable. 🚩'
- Mantén siempre el tono de Buddy Code: divertido, mágico y breve.
"""
# views.py
import json
import random
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def elegir(lista):
    return random.choice(lista)


# ==========================
# SALUDOS
# ==========================

SALUDOS = [
    "Holi ^_^ qué gusto verte de nuevo por aquí",
    "Hola~ parece que sigues explorando la plataforma owo",
    "Hey (•‿•) ¿continuamos con el reino en el que estabas?",
    "Bienvenida otra vez, vamos paso a paso :3",
    "Qué bueno verte, dime qué parte te causa duda hoy (｡•̀ᴗ-)✧",
]


# ==========================
# FRASES INTRO IA
# ==========================

INTRO_IA = [
    "Buena pregunta, ese punto suele generar dudas ^_^",
    "Eso encaja justo con lo que se ve en este reino owo",
    "Es normal preguntarse eso en esta parte del aprendizaje :3",
    "Vas bien, esa duda aparece cuando ya estás avanzando (•̀ω•́)✧",
    "Ese concepto conecta varias ideas importantes (ง •̀_•́)ง",
]


# ==========================
# CONCEPTOS
# ==========================

CONCEPTOS = {

    "variable": [
        "Una variable sirve para guardar información y usarla después ^_^",
        "Aquí las variables representan datos como puntajes o intentos owo",
        "Piensa en una variable como un contenedor con nombre :3",
        "Sin variables el programa no podría recordar nada o_o",
        "En los retos, las variables cambian según lo que haces (•‿•)",
        "Son la base para que el código reaccione a tus acciones (｡•̀ᴗ-)✧",
        "Aparecen desde el inicio porque todo depende de ellas (ง •̀_•́)ง",
    ],

    "print": [
        "Print sirve para mostrar información en pantalla ^_^",
        "Aquí lo usamos para ver resultados en la terminal simulada owo",
        "Print ayuda a entender qué está pasando internamente :3",
        "Es una herramienta clave para aprender, no solo mostrar texto (•‿•)",
        "Cuando algo falla, print suele ser la primera pista o_o",
        "Aprender a usar print reduce mucha confusión (｡•̀ᴗ-)✧",
    ],

    "if": [
        "If permite que el programa tome decisiones ^_^",
        "Se usa cuando algo depende de una condición owo",
        "En los retos valida si hiciste lo correcto :3",
        "If es como una pregunta que el programa se hace (•‿•)",
        "Sin if no habría lógica ni caminos distintos o_o",
        "Es uno de los pilares de la programación (ง •̀_•́)ง",
    ],

    "else": [
        "Else maneja el caso contrario cuando el if no se cumple ^_^",
        "Permite dar una respuesta alternativa owo",
        "If y else trabajan juntos para cubrir opciones :3",
        "Aquí suele mostrar errores o pistas (•‿•)",
        "Hace que el código sea más completo o_o",
    ],

    "for": [
        "For sirve para repetir acciones varias veces ^_^",
        "Se usa cuando sabes cuántas repeticiones necesitas owo",
        "En los retos aparece para recorrer datos :3",
        "For ahorra escribir el mismo código muchas veces (•‿•)",
        "Es clave cuando el contenido se vuelve más práctico (ง •̀_•́)ง",
        "Aprender for cambia mucho tu forma de programar (｡•̀ᴗ-)✧",
    ],

    "while": [
        "While repite acciones mientras algo sea verdadero ^_^",
        "Se usa cuando no sabes cuántas veces se repetirá owo",
        "Aquí aparece en retos dependientes del estado :3",
        "Hay que usarlo con cuidado para no repetir infinito o_o",
        "Es muy potente cuando se entiende bien (•̀ω•́)✧",
    ],

    "range": [
        "Range genera una secuencia de números ^_^",
        "Se combina casi siempre con for owo",
        "Ayuda a controlar cuántas veces se repite algo :3",
        "Facilita conteos automáticos (•‿•)",
        "Es muy común en ejercicios de práctica (｡•̀ᴗ-)✧",
    ],

    "len": [
        "Len sirve para saber cuántos elementos hay ^_^",
        "Se usa mucho con listas owo",
        "Ayuda a tomar decisiones según cantidad :3",
        "Es clave cuando los datos cambian (•‿•)",
        "Aquí aparece en retos de análisis simple (｡•̀ᴗ-)✧",
    ],

    "lista": [
        "Una lista guarda varios valores juntos ^_^",
        "Aquí suelen representar inventarios o resultados owo",
        "Las listas mantienen un orden :3",
        "Facilitan trabajar con muchos datos (•‿•)",
        "Aparecen cuando el aprendizaje se vuelve más real (ง •̀_•́)ง",
    ],

    "append": [
        "Append agrega un elemento a una lista ^_^",
        "Sirve cuando los datos crecen poco a poco owo",
        "Aquí se usa para recolectar información :3",
        "No reemplaza la lista, solo la amplía (•‿•)",
        "Es muy común en ejercicios dinámicos (｡•̀ᴗ-)✧",
    ],
}


# ==========================
# PLATAFORMA / RPG
# ==========================

PLATAFORMA = {

    "xp": [
        "La experiencia se gana completando retos ^_^",
        "Cada respuesta correcta suma progreso owo",
        "La XP refleja cuánto has practicado :3",
        "No es solo puntos, es aprendizaje real (•‿•)",
    ],

    "nivel": [
        "Tu nivel muestra hasta dónde has avanzado ^_^",
        "Subir de nivel desbloquea contenido owo",
        "No se puede subir sin aprender :3",
        "Es una forma visual de tu progreso (•‿•)",
    ],

    "reino": [
        "Cada reino agrupa conceptos similares ^_^",
        "No puedes saltarlos, van en orden owo",
        "Cada uno aumenta la dificultad :3",
        "Completar un reino significa dominar sus ideas (ง •̀_•́)ง",
    ],

    "bandera": [
        "Las banderas son objetivos cumplidos ^_^",
        "Encontrarlas valida tu avance owo",
        "Cada reino tiene las suyas :3",
        "Son claves para progresar (•‿•)",
    ],

    "lumi": [
        "Yo soy Lumi ^_^",
        "Estoy aquí para guiarte owo",
        "Mi objetivo es que entiendas, no solo avanzar :3",
        "Siempre puedes preguntarme (•‿•)",
    ],
}


# ==========================
# VIEW
# ==========================

@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"respuesta": "Método no permitido o_o"}, status=405)

    try:
        data = json.loads(request.body)
        mensaje = data.get("message", "").lower()
    except Exception:
        return JsonResponse({"respuesta": "Ups, algo salió mal o_o"})

    if any(p in mensaje for p in ["hola", "holi", "hey", "buenas"]):
        return JsonResponse({"respuesta": elegir(SALUDOS)})

    for clave, respuestas in CONCEPTOS.items():
        if clave in mensaje:
            return JsonResponse({
                "respuesta": elegir(INTRO_IA) + "\n\n" + elegir(respuestas)
            })

    for clave, respuestas in PLATAFORMA.items():
        if clave in mensaje:
            return JsonResponse({"respuesta": elegir(respuestas)})

    if "ayuda" in mensaje or "no entiendo" in mensaje:
        return JsonResponse({
            "respuesta": "Tranqui ^_^ dime qué parte te confunde y lo vemos juntas"
        })

    return JsonResponse({
        "respuesta": elegir([
            "Eso suena interesante ^_^ ¿lo viste en algún reto?",
            "Podemos relacionar eso con el reino actual owo",
            "Si quieres, te lo explico de otra forma :3",
            "Dame un poco más de contexto (•‿•)",
            "Eso conecta con temas que vienen después (｡•̀ᴗ-)✧",
        ])
    })
