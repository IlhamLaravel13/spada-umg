from django.db.models import QuerySet, Q
from django.utils import timezone
from .models import Announcement, AnnouncementRead


class AnnouncementRepository:
    def get_all(self) -> QuerySet[Announcement]:
        return Announcement.objects.select_related('created_by', 'target_class').all()

    def get_published(self) -> QuerySet[Announcement]:
        return Announcement.objects.filter(is_published=True)

    def get_by_id(self, announcement_id: int) -> Announcement | None:
        return Announcement.objects.filter(id=announcement_id).first()

    def get_important(self) -> QuerySet[Announcement]:
        now = timezone.now()
        return Announcement.objects.filter(
            is_published=True,
            is_important=True,
        ).filter(
            Q(pinned_until__isnull=True) | Q(pinned_until__gte=now)
        )

    def get_for_user(self, user) -> QuerySet[Announcement]:
        qs = self.get_published()
        if user.is_mahasiswa():
            qs = qs.filter(
                Q(audience='all') | Q(audience='mahasiswa') |
                Q(audience='class', target_class__enrollments__student=user)
            )
        elif user.is_dosen():
            qs = qs.filter(
                Q(audience='all') | Q(audience='dosen') |
                Q(audience='class', target_class__lecturer=user)
            )
        elif user.is_admin():
            qs = qs.filter(Q(audience='all') | Q(audience='admin'))
        else:
            qs = qs.filter(audience='all')
        return qs.distinct()

    def search(self, query: str) -> QuerySet[Announcement]:
        return Announcement.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )

    def create(self, **kwargs) -> Announcement:
        return Announcement.objects.create(**kwargs)

    def update(self, announcement_id: int, **kwargs) -> Announcement | None:
        updated = Announcement.objects.filter(id=announcement_id).update(**kwargs)
        if updated:
            return self.get_by_id(announcement_id)
        return None

    def delete(self, announcement_id: int) -> bool:
        return Announcement.objects.filter(id=announcement_id).delete()[0] > 0

    def count(self) -> int:
        return Announcement.objects.count()

    def count_unread(self, user) -> int:
        return self.get_for_user(user).exclude(
            reads__user=user
        ).count()


class AnnouncementReadRepository:
    def get_by_user_and_announcement(self, user, announcement_id: int) -> AnnouncementRead | None:
        return AnnouncementRead.objects.filter(user=user, announcement_id=announcement_id).first()

    def mark_as_read(self, user, announcement_id: int) -> AnnouncementRead:
        obj, _ = AnnouncementRead.objects.get_or_create(
            user=user,
            announcement_id=announcement_id,
        )
        return obj

    def mark_all_as_read(self, user) -> int:
        return AnnouncementRead.objects.filter(user=user).count()
