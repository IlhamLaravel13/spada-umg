from django.db.models import QuerySet, Prefetch
from django.utils import timezone
from .models import Material, MaterialComment, CourseProgress


class MaterialRepository:
    def get_by_id(self, material_id: int) -> Material | None:
        return Material.objects.filter(id=material_id).first()

    def get_by_class(self, class_id: int) -> QuerySet[Material]:
        return Material.objects.filter(class_meta_id=class_id)

    def get_published_by_class(self, class_id: int) -> QuerySet[Material]:
        return Material.objects.filter(class_meta_id=class_id, is_published=True)

    def get_with_comments(self, material_id: int) -> Material | None:
        return Material.objects.prefetch_related(
            Prefetch('comments', queryset=MaterialComment.objects.select_related('user'))
        ).filter(id=material_id).first()

    def search(self, class_id: int, query: str) -> QuerySet[Material]:
        return Material.objects.filter(
            class_meta_id=class_id,
            title__icontains=query
        )

    def create_material(self, **kwargs) -> Material:
        return Material.objects.create(**kwargs)

    def update_material(self, material_id: int, **kwargs) -> Material | None:
        updated = Material.objects.filter(id=material_id).update(**kwargs)
        if updated:
            return self.get_by_id(material_id)
        return None

    def delete_material(self, material_id: int) -> bool:
        return Material.objects.filter(id=material_id).delete()[0] > 0

    def reorder(self, class_id: int, material_ids: list[int]) -> bool:
        for idx, mid in enumerate(material_ids):
            Material.objects.filter(id=mid, class_meta_id=class_id).update(order=idx)
        return True

    def count_by_class(self, class_id: int) -> int:
        return Material.objects.filter(class_meta_id=class_id).count()


class MaterialCommentRepository:
    def get_for_material(self, material_id: int) -> QuerySet[MaterialComment]:
        return MaterialComment.objects.filter(material_id=material_id).select_related('user')

    def create_comment(self, material_id: int, user_id: int, comment: str) -> MaterialComment:
        return MaterialComment.objects.create(
            material_id=material_id, user_id=user_id, comment=comment
        )

    def delete_comment(self, comment_id: int, user_id: int) -> bool:
        return MaterialComment.objects.filter(id=comment_id, user_id=user_id).delete()[0] > 0


class CourseProgressRepository:
    def get_for_student(self, student_id: int, class_id: int) -> QuerySet[CourseProgress]:
        return CourseProgress.objects.filter(
            student_id=student_id, class_meta_id=class_id
        )

    def get_completed_count(self, student_id: int, class_id: int) -> int:
        return CourseProgress.objects.filter(
            student_id=student_id, class_meta_id=class_id, is_completed=True
        ).count()

    def mark_completed(self, student_id: int, material_id: int, class_id: int) -> CourseProgress:
        progress, _ = CourseProgress.objects.get_or_create(
            student_id=student_id,
            material_id=material_id,
            class_meta_id=class_id,
            defaults={'is_completed': True, 'completed_at': timezone.now()}
        )
        if not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = timezone.now()
            progress.save(update_fields=['is_completed', 'completed_at'])
        return progress

    def mark_incomplete(self, student_id: int, material_id: int) -> bool:
        return CourseProgress.objects.filter(
            student_id=student_id, material_id=material_id
        ).update(is_completed=False, completed_at=None) > 0

    def is_completed(self, student_id: int, material_id: int) -> bool:
        return CourseProgress.objects.filter(
            student_id=student_id, material_id=material_id, is_completed=True
        ).exists()
