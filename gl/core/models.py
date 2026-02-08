from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone

# ===============================
# ESTRUCTURA DE CURSOS
# ===============================

class Course(models.Model):
    CATEGORIAS = [
        ('all', '🌟 Todos los Módulos'),
        ('variables', '📦 Variables y Datos'),
        ('logica', '🛤️ Lógica (If/Else)'),
        ('loops', '🔁 Bucles (Loops)'),
        ('funciones', '🧩 Funciones'),
    ]

    title = models.CharField(max_length=200)
    min_level = models.IntegerField(default=1)
    description = models.TextField()
    image = models.ImageField(upload_to='courses/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.CharField(
        max_length=20, 
        choices=CATEGORIAS, 
        default='all',
        verbose_name="Categoría de Python"
    )
    color = models.CharField(
        max_length=20, 
        default='blue', 
        help_text="Ej: blue, pink, green, yellow, purple"
    )

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=1)
    objetivo_1 = models.CharField(max_length=300, blank=True, null=True)
    
    # --- LÓGICA DE JUEGO ---
    is_active = models.BooleanField(default=True)
    # Para crear caminos alternativos o misiones ocultas
    is_bonus = models.BooleanField(default=False) 

    # --- CONTENIDO DE EXPLICACIÓN ---
    content = models.TextField(help_text="Texto principal de la misión/lección")
    subtitle_teoria = models.CharField(max_length=200, default="¡Las variables son cajas mágicas!")
    image_lumi = models.ImageField(upload_to='lessons/', blank=True, null=True)

    # --- NÚCLEO CTF ---
    # Lo que el código debe contener para soltar la flag (validación interna)
    codigo_meta = models.CharField(max_length=100, default="print") 
    # Lo que el usuario debe escribir en el input final para ganar
    flag_secreta = models.CharField(max_length=100, default="GUMI{HOLA_MUNDO}")
    xp_leccion = models.IntegerField(default=50)
    lumi_tip = models.TextField(
        blank=True, 
        null=True, 
        help_text="Consejo que dará Gumi/Lumi si el usuario falla mucho"
    )

    # --- MINI QUIZ (Pista para la Flag) ---
    # Podemos usar el quiz no solo como examen, sino como "Hack" para obtener una pista
    quiz_pregunta = models.CharField(max_length=255, default="¿Cómo guardarías el nombre en una variable?")
    opcion_correcta = models.CharField(max_length=100, default='nombre = "Gumi"')
    opcion_incorrecta_1 = models.CharField(max_length=100, default='gumi = bear')
    opcion_incorrecta_2 = models.CharField(max_length=100, default='"Gumi" = nombre')

    def __str__(self):
        return f"{self.course.title} - {self.title}"


# ===============================
# USUARIO Y PROGRESO
# ===============================

from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    AVATAR_CHOICES = [
        ('gumi', 'Gumi (Osito)'),
        ('lumi', 'Lumi (Conejo)'),
    ]
    
    # Relación con User
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    
    # Datos adicionales
    avatar = models.CharField(max_length=10, choices=AVATAR_CHOICES, default='gumi')
    nickname = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    
    # Progreso (Cada 100 XP = 1 Nivel)
    xp = models.IntegerField(default=0)
    
    # Relación con Cursos (Asegúrate de que el modelo 'Course' esté definido o usa 'app_name.Course')
    cursos_inscritos = models.ManyToManyField('Course', blank=True, related_name="estudiantes")

    @property
    def level(self):
        """Calcula el nivel actual (Empieza en nivel 1)."""
        return (self.xp // 100) + 1

    @property
    def xp_percent(self):
        """XP acumulada dentro del nivel actual (0 a 99)."""
        return self.xp % 100

    @property
    def xp_for_next_level(self):
        """Cuánto le falta para subir al siguiente nivel."""
        return 100 - self.xp_in_level

    @property
    def rango(self):
        """Retorna un diccionario con toda la info estética del rango."""
        lvl = self.level
        
        if lvl <= 10:
            return {
                'nombre': 'Aprendiz de Gumi 🌱',
                'clase': 'bronce',
                'color': '#30abe8', # Azul Gumi
                'icon': 'potted_plant'
            }
        elif lvl <= 20:
            return {
                'nombre': 'Explorador Estelar 🚀',
                'clase': 'plata',
                'color': '#a78bfa', # Lila Lumi
                'icon': 'rocket_launch'
            }
        elif lvl <= 30:
            return {
                'nombre': 'Guardián de Código 🛡️',
                'clase': 'oro',
                'color': '#fbbf24', # Dorado
                'icon': 'shield_moon'
            }
        elif lvl <= 40:
            return {
                'nombre': 'Mago de Algoritmos ✨',
                'clase': 'platino',
                'color': '#ec4899', # Rosa Magic
                'icon': 'auto_awesome'
            }
        else:
            return {
                'nombre': 'Leyenda de Sparkle Paw 👑',
                'clase': 'diamante',
                'color': '#7c3aed', # Morado Oscuro
                'icon': 'crown'
            }

    def add_xp(self, amount):
        """Añade XP y guarda los cambios."""
        self.xp += amount
        self.save()

    def __str__(self):
        return f"{self.nickname or self.user.username} - Lvl {self.level} ({self.rango['nombre']})"

class UserLessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'lesson') # Evita duplicados de progreso


# ===============================
# LOGROS (MEDALLAS)
# ===============================
class Achievement(models.Model):
    # CORRECCIÓN: 'Course' en lugar de 'Curso'
    curso = models.ForeignKey('Course', on_delete=models.CASCADE, related_name="logros", null=True, blank=True)
    
    name = models.CharField(max_length=100, verbose_name="Nombre del Logro")
    description = models.TextField(verbose_name="¿Cómo se consigue?")
    icon_name = models.CharField(max_length=50, default="emoji_events", help_text="Nombre en Material Symbols")
    xp_reward = models.IntegerField(default=50)
    
    order = models.IntegerField(default=1)

    class Meta:
        verbose_name = "Catálogo de Logro"
        verbose_name_plural = "Catálogo de Logros"
        ordering = ['curso', 'order']

    def __str__(self):
        # CORRECCIÓN: self.curso.title en lugar de self.curso.nombre
        return f"{self.name} ({self.curso.title if self.curso else 'Global'})"


class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="achievements")
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement')


# ===============================
# MISIONES Y RETOS
# ===============================

class Mission(models.Model):
    MISSION_TYPES = [
        ('quiz', 'Quiz'),
        ('question', 'Pregunta'),
        ('code', 'Código'),
    ]

    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    mission_type = models.CharField(max_length=10, choices=MISSION_TYPES)
    xp_reward = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    
    # Relación opcional con lección
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="missions", null=True, blank=True)

    def __str__(self):
        return self.title


class UserMission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'mission')

    def save(self, *args, **kwargs):
        if self.completed and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

class Reto(models.Model):
    TIPOS_RETO = [
        ('terminal', 'Terminal Python'),
        ('pregunta', 'Pregunta Abierta'),
        ('quiz', 'Opción Múltiple'),
    ]

    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    pista = models.TextField(blank=True, null=True) # <-- NUEVO: Para ayudar sin regalar la respuesta
    icono = models.CharField(max_length=50, default='star')
    color_fondo = models.CharField(max_length=50, default='pink-100')
    xp_recompensa = models.IntegerField(default=100)
    tipo = models.CharField(max_length=20, choices=TIPOS_RETO)
    
    # Este campo guardará la respuesta correcta o las opciones del quiz
    opciones_o_respuesta = models.TextField() 
    
    # NUEVO: Para saber si la respuesta debe ser idéntica o si ignoramos mayúsculas
    es_case_sensitive = models.BooleanField(default=False) 
    
    esta_activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

class RetoCompletado(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reto = models.ForeignKey(Reto, on_delete=models.CASCADE)
    fecha_completado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'reto') # Para que no lo completen 2 veces

class ProgresoReto(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.ForeignKey)
    reto = models.ForeignKey(Reto, on_delete=models.CASCADE)
    completado = models.BooleanField(default=False)
    fecha_completado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'reto') # Para que no se repita el premio

# ===============================
# SIGNALS: CREACIÓN AUTOMÁTICA
# ===============================
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crea un perfil automáticamente cuando se registra un User"""
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Guarda el perfil automáticamente cuando se guarda el User"""
    instance.profile.save()

class Comentario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    texto = models.TextField()
    sentimiento = models.CharField(max_length=20, default='Genial')
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario de {self.usuario.username}"
    
from django.db import models
from django.contrib.auth.models import User

class Feedback(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    mensaje = models.TextField()
    sentimiento = models.CharField(max_length=50, default="Genial") # Para guardar la carita
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario de {self.usuario.username}"