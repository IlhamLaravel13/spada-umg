import logging
from django.db.models import Count
from django.db import transaction
from .repositories import LibraryItemRepository, LibraryCategoryRepository

logger = logging.getLogger(__name__)


class LibraryService:
    def __init__(self):
        self.item_repo = LibraryItemRepository()
        self.category_repo = LibraryCategoryRepository()

    def get_catalog(self, request):
        qs = self.item_repo.get_published()
        query = request.GET.get('q')
        item_type = request.GET.get('type')
        category_id = request.GET.get('category')
        faculty_id = request.GET.get('faculty')
        year = request.GET.get('year')
        language = request.GET.get('language')

        if query:
            qs = qs.filter(
                title__icontains=query
            ) | self.item_repo.get_published().filter(
                author__icontains=query
            ) | self.item_repo.get_published().filter(
                tags__icontains=query
            )

        if item_type:
            qs = qs.filter(item_type=item_type)
        if category_id:
            qs = qs.filter(category_id=category_id)
        if faculty_id:
            qs = qs.filter(faculty_id=faculty_id)
        if year:
            qs = qs.filter(publication_year=year)
        if language:
            qs = qs.filter(language__iexact=language)

        return qs.select_related('category', 'faculty').distinct()

    def get_detail(self, item_id: int):
        return self.item_repo.get_by_id(item_id)

    def increment_view(self, item_id: int):
        try:
            self.item_repo.increment_view(item_id)
        except Exception:
            pass

    def increment_download(self, item_id: int):
        try:
            self.item_repo.increment_download(item_id)
        except Exception:
            pass

    def upload_item(self, user_id: int, **data) -> dict:
        try:
            with transaction.atomic():
                item = self.item_repo.create_item(uploaded_by_id=user_id, **data)
                return {'success': True, 'item': item}
        except Exception as e:
            logger.exception("Failed to upload library item")
            return {'success': False, 'error': str(e)}

    def update_item(self, item_id: int, user_id: int, **data) -> dict:
        item = self.item_repo.get_by_id(item_id)
        if not item:
            return {'success': False, 'error': 'Item tidak ditemukan'}
        if item.uploaded_by_id and item.uploaded_by_id != user_id:
            if not hasattr(user_id, 'is_admin') or not user_id.is_admin():
                return {'success': False, 'error': 'Anda tidak berhak mengubah item ini'}
        result = self.item_repo.update_item(item_id, **data)
        if result:
            return {'success': True, 'item': result}
        return {'success': False, 'error': 'Gagal mengupdate item'}

    def delete_item(self, item_id: int, user_id: int) -> dict:
        item = self.item_repo.get_by_id(item_id)
        if not item:
            return {'success': False, 'error': 'Item tidak ditemukan'}
        if item.uploaded_by_id and item.uploaded_by_id != user_id:
            if not hasattr(user_id, 'is_admin') or not user_id.is_admin():
                return {'success': False, 'error': 'Anda tidak berhak menghapus item ini'}
        if item.file:
            try:
                import os
                if os.path.isfile(item.file.path):
                    os.remove(item.file.path)
            except (OSError, ValueError):
                pass
        if item.cover_image:
            try:
                import os
                if os.path.isfile(item.cover_image.path):
                    os.remove(item.cover_image.path)
            except (OSError, ValueError):
                pass
        self.item_repo.delete_item(item_id)
        return {'success': True}

    def get_categories_with_count(self):
        return self.category_repo.get_with_item_count()

    def get_type_summary(self):
        from .models import LibraryItem
        return LibraryItem.objects.filter(is_published=True).values('item_type').annotate(
            count=Count('id')
        ).order_by('item_type')
