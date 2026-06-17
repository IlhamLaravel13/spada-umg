from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone
from .models import User, UserSession, LoginAttempt


@receiver(post_save, sender=User)
def handle_user_created(sender, instance, created, **kwargs):
    if created:
        from .services import AuthService
        auth_service = AuthService()
        if instance.email and not instance.is_verified:
            print(f"User {instance.username} created. Send verification email to {instance.email}")


@receiver(pre_save, sender=User)
def handle_user_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            if old_instance.email != instance.email:
                instance.is_verified = False
                instance.email_verified_at = None
        except User.DoesNotExist:
            pass


@receiver(user_logged_in)
def handle_user_login(sender, request, user, **kwargs):
    user.last_login = timezone.now()
    user.last_activity = timezone.now()
    user.save(update_fields=['last_login', 'last_activity'])


@receiver(user_logged_out)
def handle_user_logout(sender, request, user, **kwargs):
    if user:
        session_key = request.session.session_key
        if session_key:
            UserSession.objects.filter(
                user=user, session_key=session_key, is_active=True
            ).update(is_active=False)
