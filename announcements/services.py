import logging
from django.db.models import Q
from django.utils import timezone

from .repositories import AnnouncementRepository, AnnouncementReadRepository

logger = logging.getLogger(__name__)


class AnnouncementService:
    def __init__(self):
        self.repo = AnnouncementRepository()
        self.read_repo = AnnouncementReadRepository()

    def get_all(self):
        return self.repo.get_all()

    def get_published(self):
        return self.repo.get_published()

    def get_by_id(self, announcement_id: int):
        return self.repo.get_by_id(announcement_id)

    def get_important(self):
        return self.repo.get_important()

    def get_for_user(self, user):
        return self.repo.get_for_user(user)

    def create(self, **kwargs) -> dict:
        try:
            announcement = self.repo.create(**kwargs)
            return {'success': True, 'data': announcement}
        except Exception as e:
            logger.exception("Failed to create announcement")
            return {'success': False, 'error': str(e)}

    def update(self, announcement_id: int, **kwargs) -> dict:
        try:
            announcement = self.repo.update(announcement_id, **kwargs)
            if announcement:
                return {'success': True, 'data': announcement}
            return {'success': False, 'error': 'Announcement not found'}
        except Exception as e:
            logger.exception("Failed to update announcement")
            return {'success': False, 'error': str(e)}

    def delete(self, announcement_id: int) -> dict:
        try:
            if self.repo.delete(announcement_id):
                return {'success': True, 'message': 'Announcement deleted successfully'}
            return {'success': False, 'error': 'Announcement not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def toggle_publish(self, announcement_id: int) -> dict:
        announcement = self.repo.get_by_id(announcement_id)
        if not announcement:
            return {'success': False, 'error': 'Announcement not found'}
        return self.update(announcement_id, is_published=not announcement.is_published)

    def toggle_important(self, announcement_id: int) -> dict:
        announcement = self.repo.get_by_id(announcement_id)
        if not announcement:
            return {'success': False, 'error': 'Announcement not found'}
        return self.update(announcement_id, is_important=not announcement.is_important)

    def mark_as_read(self, user, announcement_id: int) -> dict:
        try:
            announcement = self.repo.get_by_id(announcement_id)
            if not announcement:
                return {'success': False, 'error': 'Announcement not found'}
            self.read_repo.mark_as_read(user, announcement_id)
            return {'success': True, 'message': 'Marked as read'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def mark_all_as_read(self, user) -> dict:
        try:
            count = self.read_repo.mark_all_as_read(user)
            return {'success': True, 'message': f'{count} announcements marked as read'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_unread_count(self, user) -> int:
        return self.repo.count_unread(user)

    def get_unread_announcements(self, user):
        return self.repo.get_for_user(user).exclude(reads__user=user)
