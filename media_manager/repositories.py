from django.db.models import QuerySet, Q
from .models import MediaFile


class MediaFileRepository:
    def get_all(self) -> QuerySet[MediaFile]:
        return MediaFile.objects.select_related('uploaded_by').all()

    def get_public(self) -> QuerySet[MediaFile]:
        return self.get_all().filter(is_public=True)

    def get_by_id(self, media_id: int) -> MediaFile | None:
        return MediaFile.objects.filter(id=media_id).select_related('uploaded_by').first()

    def get_by_type(self, file_type: str) -> QuerySet[MediaFile]:
        return self.get_all().filter(file_type=file_type)

    def get_by_uploader(self, user_id: int) -> QuerySet[MediaFile]:
        return self.get_all().filter(uploaded_by_id=user_id)

    def search(self, query: str) -> QuerySet[MediaFile]:
        return self.get_all().filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query) |
            Q(alt_text__icontains=query)
        )

    def create(self, **kwargs) -> MediaFile:
        return MediaFile.objects.create(**kwargs)

    def update(self, media_id: int, **kwargs) -> MediaFile | None:
        updated = MediaFile.objects.filter(id=media_id).update(**kwargs)
        if updated:
            return self.get_by_id(media_id)
        return None

    def delete(self, media_id: int) -> bool:
        return MediaFile.objects.filter(id=media_id).delete()[0] > 0

    def increment_download(self, media_id: int) -> bool:
        updated = MediaFile.objects.filter(id=media_id).update(download_count=models.F('download_count') + 1)
        return updated > 0
