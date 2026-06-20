from django.db.models import QuerySet
from django.db.utils import OperationalError
from django.utils import timezone
from .models import ActivityLog, SystemConfig


class ActivityLogRepository:
    def get_all(self) -> QuerySet[ActivityLog]:
        return ActivityLog.objects.all()

    def get_by_id(self, log_id: int) -> ActivityLog | None:
        return ActivityLog.objects.filter(id=log_id).first()

    def get_by_user(self, user_id: int) -> QuerySet[ActivityLog]:
        return ActivityLog.objects.filter(user_id=user_id)

    def get_by_action(self, action: str) -> QuerySet[ActivityLog]:
        return ActivityLog.objects.filter(action=action)

    def get_by_model(self, model_name: str) -> QuerySet[ActivityLog]:
        return ActivityLog.objects.filter(model_name__iexact=model_name)

    def get_recent(self, limit: int = 50) -> QuerySet[ActivityLog]:
        return ActivityLog.objects.all()[:limit]

    def get_user_recent_actions(self, user_id: int, limit: int = 20) -> QuerySet[ActivityLog]:
        return ActivityLog.objects.filter(user_id=user_id)[:limit]

    def create_log(self, user, action: str, model_name: str,
                   object_id: str = '', description: str = '',
                   ip_address: str = None, user_agent: str = '') -> ActivityLog:
        return ActivityLog.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=object_id,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def delete_older_than(self, days: int = 90) -> int:
        cutoff = timezone.now() - timezone.timedelta(days=days)
        deleted, _ = ActivityLog.objects.filter(created_at__lt=cutoff).delete()
        return deleted

    def count_by_action(self) -> dict:
        from django.db.models import Count
        return dict(ActivityLog.objects.values_list('action').annotate(count=Count('id')))


class SystemConfigRepository:
    def get_all(self) -> QuerySet[SystemConfig]:
        return SystemConfig.objects.all()

    def get_by_key(self, key: str) -> SystemConfig | None:
        return SystemConfig.objects.filter(key=key).first()

    def get_public(self) -> QuerySet[SystemConfig]:
        return SystemConfig.objects.filter(is_public=True)

    def get_value(self, key: str, default: str = '') -> str:
        try:
            config = self.get_by_key(key)
            return config.value if config else default
        except OperationalError:
            return default

    def set_value(self, key: str, value: str, description: str = '',
                  is_public: bool = False) -> SystemConfig:
        config, created = SystemConfig.objects.update_or_create(
            key=key,
            defaults={
                'value': value,
                'description': description,
                'is_public': is_public,
            }
        )
        return config

    def delete_by_key(self, key: str) -> bool:
        deleted, _ = SystemConfig.objects.filter(key=key).delete()
        return deleted > 0

    def get_group(self, prefix: str) -> dict:
        configs = SystemConfig.objects.filter(key__startswith=prefix)
        return {c.key: c.value for c in configs}
