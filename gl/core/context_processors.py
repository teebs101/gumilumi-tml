from .models import UserLessonProgress, Lesson

def global_context(request):
    if request.user.is_authenticated:
        # Busca la última lección completada por el usuario
        ultimo = UserLessonProgress.objects.filter(user=request.user, completed=True).order_by('-completed_at').first()
        if ultimo:
            # Busca la siguiente lección en el mismo curso
            proxima = Lesson.objects.filter(course=ultimo.lesson.course, order__gt=ultimo.lesson.order).first()
            if not proxima:
                # Si terminó el curso, busca la primera de cualquier otro curso
                proxima = Lesson.objects.exclude(course=ultimo.lesson.course).first()
        else:
            # Si es nuevo, la primera lección de todas
            proxima = Lesson.objects.order_by('course__id', 'order').first()
        
        return {'proxima_leccion': proxima}
    return {}