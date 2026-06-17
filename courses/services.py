import os
import magic
from django.conf import settings
from django.db import transaction
from .repositories import MaterialRepository, MaterialCommentRepository, CourseProgressRepository
from academics.repositories import ClassRepository
from .models import Material


MATERIAL_TYPE_MAP = {
    'application/pdf': 'pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'application/msword': 'docx',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
    'application/vnd.ms-powerpoint': 'pptx',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
    'application/vnd.ms-excel': 'xlsx',
    'video/mp4': 'video',
    'video/x-msvideo': 'video',
    'video/quicktime': 'video',
    'audio/mpeg': 'audio',
    'audio/mp3': 'audio',
    'audio/wav': 'audio',
    'image/jpeg': 'image',
    'image/png': 'image',
    'image/gif': 'image',
    'image/webp': 'image',
    'application/zip': 'archive',
    'application/x-rar-compressed': 'archive',
    'application/x-tar': 'archive',
    'application/gzip': 'archive',
}

FILE_SIZE_LIMIT = 50 * 1024 * 1024  # 50MB


class MaterialService:
    def __init__(self):
        self.material_repo = MaterialRepository()
        self.comment_repo = MaterialCommentRepository()
        self.class_repo = ClassRepository()

    def get_class_materials(self, class_id: int, is_dosen: bool = False):
        if is_dosen:
            return self.material_repo.get_by_class(class_id)
        return self.material_repo.get_published_by_class(class_id)

    def get_material_detail(self, material_id: int):
        return self.material_repo.get_with_comments(material_id)

    def upload_material(self, class_id: int, uploaded_by_id: int, **data) -> dict:
        class_obj = self.class_repo.get_by_id(class_id)
        if not class_obj:
            return {'success': False, 'error': 'Class tidak ditemukan'}

        uploaded_file = data.pop('file', None)
        file_type = data.get('file_type', 'other')
        file_size = 0

        if uploaded_file:
            if uploaded_file.size > FILE_SIZE_LIMIT:
                return {'success': False, 'error': 'Ukuran file maksimal 50MB'}
            file_size = uploaded_file.size

            detected = self._detect_file_type(uploaded_file)
            if detected != 'other':
                file_type = detected
                data['file_type'] = detected

        try:
            with transaction.atomic():
                material = self.material_repo.create_material(
                    class_meta_id=class_id,
                    uploaded_by_id=uploaded_by_id,
                    file=uploaded_file or '',
                    file_size=file_size,
                    **data
                )
                return {'success': True, 'material': material}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_material(self, material_id: int, user_id: int, **data) -> dict:
        material = self.material_repo.get_by_id(material_id)
        if not material:
            return {'success': False, 'error': 'Material tidak ditemukan'}
        if material.uploaded_by_id != user_id:
            return {'success': False, 'error': 'Anda tidak berhak mengubah material ini'}

        uploaded_file = data.pop('file', None)
        if uploaded_file:
            if uploaded_file.size > FILE_SIZE_LIMIT:
                return {'success': False, 'error': 'Ukuran file maksimal 50MB'}
            data['file'] = uploaded_file
            data['file_size'] = uploaded_file.size
            detected = self._detect_file_type(uploaded_file)
            if detected != 'other':
                data['file_type'] = detected

        result = self.material_repo.update_material(material_id, **data)
        if result:
            return {'success': True, 'material': result}
        return {'success': False, 'error': 'Gagal mengupdate material'}

    def delete_material(self, material_id: int, user_id: int) -> dict:
        material = self.material_repo.get_by_id(material_id)
        if not material:
            return {'success': False, 'error': 'Material tidak ditemukan'}
        if material.uploaded_by_id != user_id:
            return {'success': False, 'error': 'Anda tidak berhak menghapus material ini'}

        if material.file and os.path.isfile(material.file.path):
            try:
                os.remove(material.file.path)
            except OSError:
                pass

        self.material_repo.delete_material(material_id)
        return {'success': True, 'message': 'Material berhasil dihapus'}

    def toggle_publish(self, material_id: int) -> dict:
        material = self.material_repo.get_by_id(material_id)
        if not material:
            return {'success': False, 'error': 'Material tidak ditemukan'}
        new_status = not material.is_published
        self.material_repo.update_material(material_id, is_published=new_status)
        return {'success': True, 'is_published': new_status}

    def add_comment(self, material_id: int, user_id: int, comment: str) -> dict:
        material = self.material_repo.get_by_id(material_id)
        if not material:
            return {'success': False, 'error': 'Material tidak ditemukan'}
        if not comment.strip():
            return {'success': False, 'error': 'Komentar tidak boleh kosong'}
        comment_obj = self.comment_repo.create_comment(material_id, user_id, comment)
        return {'success': True, 'comment': comment_obj}

    def _detect_file_type(self, uploaded_file) -> str:
        try:
            uploaded_file.seek(0)
            mime_type = magic.from_buffer(uploaded_file.read(2048), mime=True)
            uploaded_file.seek(0)
            return MATERIAL_TYPE_MAP.get(mime_type, 'other')
        except Exception:
            uploaded_file.seek(0)
            return 'other'


class CourseProgressService:
    def __init__(self):
        self.progress_repo = CourseProgressRepository()
        self.material_repo = MaterialRepository()

    def get_progress(self, student_id: int, class_id: int):
        return self.progress_repo.get_for_student(student_id, class_id)

    def get_completion_stats(self, student_id: int, class_id: int) -> dict:
        total = self.material_repo.count_by_class(class_id)
        completed = self.progress_repo.get_completed_count(student_id, class_id)
        return {
            'total': total,
            'completed': completed,
            'percentage': round((completed / total * 100), 1) if total > 0 else 0,
        }

    def mark_completed(self, student_id: int, material_id: int, class_id: int) -> dict:
        material = self.material_repo.get_by_id(material_id)
        if not material:
            return {'success': False, 'error': 'Material tidak ditemukan'}
        if material.class_meta_id != class_id:
            return {'success': False, 'error': 'Material tidak sesuai dengan kelas'}
        self.progress_repo.mark_completed(student_id, material_id, class_id)
        return {'success': True, 'message': 'Progress diperbarui'}

    def mark_incomplete(self, student_id: int, material_id: int) -> dict:
        self.progress_repo.mark_incomplete(student_id, material_id)
        return {'success': True, 'message': 'Progress direset'}
