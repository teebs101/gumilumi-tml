from django.contrib import admin
from .models import (
    Course, Lesson, Achievement, UserAchievement, 
    UserLessonProgress, Profile, Mission, UserMission, 
    Reto, RetoCompletado, Feedback
)

# --- CONFIGURACIÓN DE CURSOS Y LECCIONES ---

class LessonInline(admin.TabularInline):
    """Esto permite editar lecciones dentro de la página del Curso"""
    model = Lesson
    extra = 5 # Muestra 5 espacios para las 5 lecciones del reino
    fields = ('title', 'order', 'xp_leccion', 'flag_secreta')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'min_level', 'color')
    list_filter = ('category', 'min_level')
    list_editable = ('category', 'color', 'min_level')
    inlines = [LessonInline] # <--- ¡Mágico! Añade lecciones desde aquí
    search_fields = ('title',)

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order", "xp_leccion")
    list_filter = ("course",)
    search_fields = ("title", "content")

# --- PERFIL DE USUARIO (DASHBOARD ADMINISTRATIVO) ---

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # Combiné tus dos list_display en uno solo y añadí el rango
    list_display = ('user', 'nickname', 'avatar', 'level', 'xp', 'get_rango')
    list_filter = ('avatar', 'xp')
    search_fields = ('user__username', 'nickname', 'user__first_name', 'user__last_name')
    filter_horizontal = ('cursos_inscritos',)
    
    # Campos que no se pueden editar manualmente (calculados)
    readonly_fields = ('level', 'get_rango')

    def get_rango(self, obj):
        # Muestra el nombre del rango desde el diccionario que hicimos en models.py
        return obj.rango['nombre']
    get_rango.short_description = 'Rango Actual'

# --- LOGROS Y MISIONES ---

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'curso', 'order', 'xp_reward', 'icon_name')
    list_editable = ('xp_reward', 'icon_name', 'order')
    list_filter = ('curso',)

@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'earned_at')
    list_filter = ('user', 'achievement')

@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ("title", "mission_type", "xp_reward", "is_active")
    list_filter = ("mission_type", "is_active")
    search_fields = ("title",)

@admin.register(UserMission)
class UserMissionAdmin(admin.ModelAdmin):
    list_display = ("user", "mission", "completed", "completed_at")
    list_filter = ("completed", "completed_at")

# --- RETOS Y FEEDBACK ---

@admin.register(Reto)
class RetoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'xp_recompensa', 'esta_activo')
    list_editable = ('esta_activo', 'xp_recompensa')

@admin.register(RetoCompletado)
class RetoCompletadoAdmin(admin.ModelAdmin):
    list_display = ('user', 'reto', 'fecha_completado')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'mensaje', 'fecha')
    readonly_fields = ('fecha',)

@admin.register(UserLessonProgress)
class UserLessonProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'completed', 'completed_at')
    list_filter = ('completed', 'lesson__course')

# --- PERSONALIZACIÓN DEL HEADER ---
admin.site.site_header = "Gumi & Lumi Academy: Torre de Control ✨"
admin.site.site_title = "Gumi & Lumi Admin"
admin.site.index_title = "¡Bienvenida, mor! Aquí gestionas la magia del código 🐻🐰"