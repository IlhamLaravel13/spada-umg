from django.db.models import QuerySet, Q, Count
from .models import LibraryItem, LibraryCategory


class LibraryCategoryRepository:
    def get_all(self) -> QuerySet[LibraryCategory]:
        return LibraryCategory.objects.all()

    def get_active(self) -> QuerySet[LibraryCategory]:
        return LibraryCategory.objects.filter(is_active=True)

    def get_by_id(self, category_id: int) -> LibraryCategory | None:
        return LibraryCategory.objects.filter(id=category_id).first()

    def get_by_slug(self, slug: str) -> LibraryCategory | None:
        return LibraryCategory.objects.filter(slug=slug, is_active=True).first()

    def get_with_item_count(self) -> QuerySet[LibraryCategory]:
        return LibraryCategory.objects.filter(is_active=True).annotate(
            item_count=Count('libraryitem', filter=Q(libraryitem__is_published=True))
        )


class LibraryItemRepository:
    def get_all(self) -> QuerySet[LibraryItem]:
        return LibraryItem.objects.select_related(
            'category', 'faculty', 'study_program', 'uploaded_by'
        )

    def get_published(self) -> QuerySet[LibraryItem]:
        return self.get_all().filter(is_published=True)

    def get_by_id(self, item_id: int) -> LibraryItem | None:
        return self.get_all().filter(id=item_id).first()

    def get_by_category(self, category_id: int) -> QuerySet[LibraryItem]:
        return self.get_published().filter(category_id=category_id)

    def get_by_type(self, item_type: str) -> QuerySet[LibraryItem]:
        return self.get_published().filter(item_type=item_type)

    def get_by_faculty(self, faculty_id: int) -> QuerySet[LibraryItem]:
        return self.get_published().filter(faculty_id=faculty_id)

    def get_latest(self, limit: int = 6) -> QuerySet[LibraryItem]:
        return self.get_published().order_by('-created_at')[:limit]

    def get_popular(self, limit: int = 6) -> QuerySet[LibraryItem]:
        return self.get_published().order_by('-download_count')[:limit]

    def search(self, query: str) -> QuerySet[LibraryItem]:
        return self.get_published().filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(description__icontains=query) |
            Q(publisher__icontains=query) |
            Q(tags__icontains=query) |
            Q(isbn__icontains=query)
        )

    def filter(self, item_type: str = None, category_id: int = None,
               faculty_id: int = None, study_program_id: int = None,
               year: int = None, language: str = None) -> QuerySet[LibraryItem]:
        qs = self.get_published()
        if item_type:
            qs = qs.filter(item_type=item_type)
        if category_id:
            qs = qs.filter(category_id=category_id)
        if faculty_id:
            qs = qs.filter(faculty_id=faculty_id)
        if study_program_id:
            qs = qs.filter(study_program_id=study_program_id)
        if year:
            qs = qs.filter(publication_year=year)
        if language:
            qs = qs.filter(language__iexact=language)
        return qs

    def create_item(self, **kwargs) -> LibraryItem:
        return LibraryItem.objects.create(**kwargs)

    def update_item(self, item_id: int, **kwargs) -> LibraryItem | None:
        updated = LibraryItem.objects.filter(id=item_id).update(**kwargs)
        if updated:
            return self.get_by_id(item_id)
        return None

    def delete_item(self, item_id: int) -> bool:
        return LibraryItem.objects.filter(id=item_id).delete()[0] > 0

    def increment_download(self, item_id: int):
        LibraryItem.objects.filter(id=item_id).update(download_count=Count('download_count') + 1)

    def increment_view(self, item_id: int):
        LibraryItem.objects.filter(id=item_id).update(view_count=Count('view_count') + 1)
