from django.db.models import QuerySet, Q
from .models import Notification


class NotificationRepository:
    def get_for_user(self, user) -> QuerySet[Notification]:
        return Notification.objects.filter(recipient=user).select_related('recipient')

    def get_unread(self, user) -> QuerySet[Notification]:
        return Notification.objects.filter(recipient=user, is_read=False).select_related('recipient')

    def get_by_id(self, notification_id: int) -> Notification | None:
        return Notification.objects.filter(id=notification_id).first()

    def get_unread_count(self, user) -> int:
        return Notification.objects.filter(recipient=user, is_read=False).count()

    def get_paginated(self, user, page: int = 1, per_page: int = 20):
        from django.core.paginator import Paginator
        qs = self.get_for_user(user)
        paginator = Paginator(qs, per_page)
        return paginator.get_page(page), paginator

    def create(self, **kwargs) -> Notification:
        return Notification.objects.create(**kwargs)

    def bulk_create(self, notifications: list[Notification]) -> list[Notification]:
        return Notification.objects.bulk_create(notifications)

    def mark_read(self, notification_id: int, user) -> Notification | None:
        from django.utils import timezone
        updated = Notification.objects.filter(
            id=notification_id, recipient=user
        ).update(is_read=True, read_at=timezone.now())
        if updated:
            return self.get_by_id(notification_id)
        return None

    def mark_all_read(self, user) -> int:
        from django.utils import timezone
        return Notification.objects.filter(recipient=user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )

    def delete_old(self, days: int = 90):
        from django.utils import timezone
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return Notification.objects.filter(created_at__lt=cutoff).delete()[0]
