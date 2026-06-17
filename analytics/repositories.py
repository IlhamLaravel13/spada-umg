from django.db.models import QuerySet, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta

from .models import AnalyticsCache, UserActivity
from accounts.models import User
from academics.models import Course, Enrollment, Class as ClassModel


class AnalyticsCacheRepository:
    def get(self, key: str) -> AnalyticsCache | None:
        return AnalyticsCache.objects.filter(
            key=key, expires_at__gt=timezone.now()
        ).first()

    def set(self, key: str, data: dict, ttl_minutes: int = 60) -> AnalyticsCache:
        obj, _ = AnalyticsCache.objects.update_or_create(
            key=key,
            defaults={
                'data': data,
                'expires_at': timezone.now() + timedelta(minutes=ttl_minutes),
            }
        )
        return obj

    def delete_expired(self) -> int:
        return AnalyticsCache.objects.filter(expires_at__lte=timezone.now()).delete()[0]


class UserActivityRepository:
    def log(self, user, action: str, metadata: dict = None,
            ip_address: str = None) -> UserActivity:
        return UserActivity.objects.create(
            user=user, action=action,
            metadata=metadata or {},
            ip_address=ip_address,
        )

    def get_recent(self, limit: int = 50) -> QuerySet[UserActivity]:
        return UserActivity.objects.select_related('user')[:limit]

    def get_by_user(self, user) -> QuerySet[UserActivity]:
        return UserActivity.objects.filter(user=user)

    def get_by_action(self, action: str, days: int = 30) -> QuerySet[UserActivity]:
        cutoff = timezone.now() - timedelta(days=days)
        return UserActivity.objects.filter(action=action, created_at__gte=cutoff)

    def count_by_action(self, days: int = 30) -> dict:
        cutoff = timezone.now() - timedelta(days=days)
        return dict(
            UserActivity.objects.filter(created_at__gte=cutoff)
            .values('action')
            .annotate(count=Count('id'))
            .values_list('action', 'count')
        )

    def get_active_users_count(self, days: int = 7) -> int:
        cutoff = timezone.now() - timedelta(days=days)
        return UserActivity.objects.filter(
            created_at__gte=cutoff
        ).values('user').distinct().count()

    def get_daily_activity(self, days: int = 30):
        cutoff = timezone.now() - timedelta(days=days)
        from django.db.models.functions import TruncDate
        return list(
            UserActivity.objects.filter(created_at__gte=cutoff)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
