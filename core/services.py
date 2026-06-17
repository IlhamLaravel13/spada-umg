from django.db.models import Q
from django.conf import settings
from .repositories import ActivityLogRepository, SystemConfigRepository


class ActivityLogService:
    def __init__(self):
        self.repo = ActivityLogRepository()

    def log(self, user, action: str, model_name: str, object_id: str = '',
            description: str = '', ip_address: str = None, user_agent: str = ''):
        return self.repo.create_log(
            user=user,
            action=action,
            model_name=model_name,
            object_id=object_id,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def get_user_activity(self, user_id: int, limit: int = 20):
        return self.repo.get_user_recent_actions(user_id, limit)

    def get_recent_activity(self, limit: int = 50):
        return self.repo.get_recent(limit)

    def get_activity_summary(self, days: int = 7):
        from django.utils import timezone
        from django.db.models import Count
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return ActivityLogRepository().get_all().filter(
            created_at__gte=cutoff
        ).values('action').annotate(
            count=Count('id')
        ).order_by('-count')

    def cleanup_old_logs(self, days: int = 90):
        return self.repo.delete_older_than(days)


class SystemConfigService:
    def __init__(self):
        self.repo = SystemConfigRepository()

    def get(self, key: str, default: str = '') -> str:
        return self.repo.get_value(key, default)

    def set(self, key: str, value: str, description: str = '',
            is_public: bool = False):
        return self.repo.set_value(key, value, description, is_public)

    def get_all(self):
        return self.repo.get_all()

    def get_public_configs(self):
        return self.repo.get_public()

    def get_group(self, prefix: str) -> dict:
        return self.repo.get_group(prefix)

    def delete(self, key: str) -> bool:
        return self.repo.delete_by_key(key)


class SearchService:
    MAX_RESULTS_PER_MODEL = 10

    def search_all(self, query: str, user=None) -> dict:
        if not query or len(query.strip()) < 2:
            return {'query': query, 'results': {}, 'total': 0}
        query = query.strip()
        results = {}
        total = 0
        users_result = self._search_users(query) if user and user.is_staff else []
        if users_result:
            results['users'] = users_result
            total += len(users_result)
        courses_result = self._search_courses(query)
        if courses_result:
            results['courses'] = courses_result
            total += len(courses_result)
        materials_result = self._search_materials(query)
        if materials_result:
            results['materials'] = materials_result
            total += len(materials_result)
        announcements_result = self._search_announcements(query)
        if announcements_result:
            results['announcements'] = announcements_result
            total += len(announcements_result)
        return {'query': query, 'results': results, 'total': total}

    def _search_users(self, query: str) -> list:
        try:
            from accounts.models import User
            if 'postgresql' in settings.DATABASES.get('default', {}).get('ENGINE', ''):
                from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
                vector = SearchVector('username', 'email', 'first_name', 'last_name', 'nim', 'nidn')
                search_query = SearchQuery(query)
                qs = User.objects.annotate(
                    rank=SearchRank(vector, search_query)
                ).filter(rank__gte=0.1).order_by('-rank')[:self.MAX_RESULTS_PER_MODEL]
            else:
                qs = User.objects.filter(
                    Q(username__icontains=query) |
                    Q(email__icontains=query) |
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query) |
                    Q(nim__icontains=query) |
                    Q(nidn__icontains=query)
                )[:self.MAX_RESULTS_PER_MODEL]
            return [
                {
                    'id': u.id,
                    'name': u.get_full_name() or u.username,
                    'email': u.email,
                    'role': u.get_role_display(),
                    'avatar': u.avatar.url if u.avatar else None,
                    'url': f'/accounts/profile/{u.id}/',
                }
                for u in qs
            ]
        except Exception:
            return []

    def _search_courses(self, query: str) -> list:
        try:
            from academics.models import Course
            qs = Course.objects.filter(
                Q(code__icontains=query) |
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )[:self.MAX_RESULTS_PER_MODEL]
            return [
                {
                    'id': c.id,
                    'code': c.code,
                    'name': c.name,
                    'description': c.description[:200] if c.description else '',
                    'url': f'/courses/{c.id}/',
                }
                for c in qs
            ]
        except Exception:
            return []

    def _search_materials(self, query: str) -> list:
        try:
            from courses.models import Material
            qs = Material.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )[:self.MAX_RESULTS_PER_MODEL]
            return [
                {
                    'id': m.id,
                    'title': m.title,
                    'description': m.description[:200] if m.description else '',
                    'course': m.course.name if hasattr(m, 'course') and m.course else '',
                    'url': f'/courses/{m.course_id}/materials/{m.id}/' if m.course_id else '#',
                }
                for m in qs
            ]
        except Exception:
            return []

    def _search_announcements(self, query: str) -> list:
        try:
            from announcements.models import Announcement
            qs = Announcement.objects.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query)
            )[:self.MAX_RESULTS_PER_MODEL]
            return [
                {
                    'id': a.id,
                    'title': a.title,
                    'content': a.content[:200] if a.content else '',
                    'created_at': a.created_at.isoformat() if hasattr(a, 'created_at') else '',
                    'url': f'/announcements/{a.id}/',
                }
                for a in qs
            ]
        except Exception:
            return []
