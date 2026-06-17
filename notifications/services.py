import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .repositories import NotificationRepository
from .models import Notification

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.repo = NotificationRepository()

    def create(self, recipient, notification_type: str, title: str, message: str,
               link: str = '', is_important: bool = False, send_email: bool = False) -> dict:
        try:
            notification = self.repo.create(
                recipient=recipient,
                notification_type=notification_type,
                title=title,
                message=message,
                link=link,
                is_important=is_important,
            )
            if send_email and recipient.email:
                self.send_email(notification)
            return {'success': True, 'data': notification}
        except Exception as e:
            logger.exception("Failed to create notification")
            return {'success': False, 'error': str(e)}

    def bulk_create(self, notifications_data: list[dict]) -> dict:
        try:
            objs = [Notification(**data) for data in notifications_data]
            created = self.repo.bulk_create(objs)
            return {'success': True, 'count': len(created)}
        except Exception as e:
            logger.exception("Failed to bulk create notifications")
            return {'success': False, 'error': str(e)}

    def mark_read(self, notification_id: int, user) -> dict:
        notification = self.repo.mark_read(notification_id, user)
        if notification:
            return {'success': True, 'data': notification}
        return {'success': False, 'error': 'Notification not found'}

    def mark_all_read(self, user) -> dict:
        count = self.repo.mark_all_read(user)
        return {'success': True, 'count': count}

    def get_unread_count(self, user) -> int:
        return self.repo.get_unread_count(user)

    def get_paginated(self, user, page: int = 1, per_page: int = 20):
        return self.repo.get_paginated(user, page, per_page)

    def send_email(self, notification: Notification) -> bool:
        try:
            subject = f"[SPADA UMG] {notification.title}"
            html_message = render_to_string('notifications/email/notification_email.html', {
                'notification': notification,
                'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else '',
            })
            plain_message = strip_tags(html_message)
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.recipient.email],
                html_message=html_message,
                fail_silently=True,
            )
            if not notification.sent_email:
                Notification.objects.filter(id=notification.id).update(sent_email=True)
            return True
        except Exception as e:
            logger.exception("Failed to send notification email")
            return False

    def clean_old_notifications(self, days: int = 90) -> int:
        return self.repo.delete_old(days)
