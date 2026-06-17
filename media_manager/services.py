import logging
import mimetypes
from .repositories import MediaFileRepository

logger = logging.getLogger(__name__)


class MediaFileService:
    def __init__(self):
        self.repo = MediaFileRepository()

    def get_all(self):
        return self.repo.get_all()

    def get_public(self):
        return self.repo.get_public()

    def get_by_id(self, media_id: int):
        return self.repo.get_by_id(media_id)

    def get_by_type(self, file_type: str):
        return self.repo.get_by_type(file_type)

    def get_by_uploader(self, user_id: int):
        return self.repo.get_by_uploader(user_id)

    def search(self, query: str):
        return self.repo.search(query)

    def _infer_file_type(self, mime_type: str) -> str:
        if not mime_type:
            return 'other'
        mime_lower = mime_type.lower()
        if mime_lower.startswith('image/'):
            return 'image'
        elif mime_lower.startswith('video/'):
            return 'video'
        elif mime_lower.startswith('audio/'):
            return 'audio'
        elif mime_lower in ('application/pdf', 'application/msword',
                            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                            'application/vnd.ms-excel',
                            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            'text/plain', 'text/html', 'text/csv'):
            return 'document'
        elif any(x in mime_lower for x in ('zip', 'rar', 'tar', 'gzip', '7z', 'compress')):
            return 'archive'
        return 'other'

    def upload(self, **kwargs) -> dict:
        try:
            file_obj = kwargs.get('file')
            if file_obj:
                kwargs['file_size'] = file_obj.size
                mime_type, _ = mimetypes.guess_type(file_obj.name)
                kwargs['mime_type'] = mime_type or 'application/octet-stream'
                if 'file_type' not in kwargs or not kwargs['file_type']:
                    kwargs['file_type'] = self._infer_file_type(kwargs['mime_type'])
            media = self.repo.create(**kwargs)
            return {'success': True, 'data': media}
        except Exception as e:
            logger.exception("Failed to upload media file")
            return {'success': False, 'error': str(e)}

    def update(self, media_id: int, **kwargs) -> dict:
        try:
            media = self.repo.update(media_id, **kwargs)
            if media:
                return {'success': True, 'data': media}
            return {'success': False, 'error': 'Media file not found'}
        except Exception as e:
            logger.exception("Failed to update media file")
            return {'success': False, 'error': str(e)}

    def delete(self, media_id: int) -> dict:
        try:
            media = self.repo.get_by_id(media_id)
            if not media:
                return {'success': False, 'error': 'Media file not found'}
            if media.file:
                storage = media.file.storage
                if storage.exists(media.file.name):
                    storage.delete(media.file.name)
            if media.thumbnail:
                storage = media.thumbnail.storage
                if storage.exists(media.thumbnail.name):
                    storage.delete(media.thumbnail.name)
            if self.repo.delete(media_id):
                return {'success': True, 'message': 'Media file deleted successfully'}
            return {'success': False, 'error': 'Failed to delete'}
        except Exception as e:
            logger.exception("Failed to delete media file")
            return {'success': False, 'error': str(e)}

    def increment_download(self, media_id: int) -> dict:
        try:
            if self.repo.increment_download(media_id):
                return {'success': True}
            return {'success': False, 'error': 'Media file not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
