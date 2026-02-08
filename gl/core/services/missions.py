from django.utils import timezone
from core.models import UserMission, UserAchievement, Achievement

def complete_mission(user, mission):
    user_mission, created = UserMission.objects.get_or_create(
        user=user,
        mission=mission
    )

    if user_mission.completed:
        return False

    user_mission.completed = True
    user_mission.completed_at = timezone.now()
    user_mission.save()

    # XP
    profile = user.profile
    profile.add_xp(mission.xp_reward)

    # Logros
    unlock_achievements(user)

    return True


def unlock_achievements(user):
    completed_missions = UserMission.objects.filter(
        user=user,
        completed=True
    ).count()

    for achievement in Achievement.objects.all():
        if completed_missions >= achievement.xp_reward:
            UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )
