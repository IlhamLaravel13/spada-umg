import logging
from .repositories import SiteSettingRepository

logger = logging.getLogger(__name__)


class SiteSettingService:
    def __init__(self):
        self.repo = SiteSettingRepository()

    def get_all(self):
        return self.repo.get_all()

    def get_by_id(self, setting_id: int):
        return self.repo.get_by_id(setting_id)

    def get_by_key(self, key: str):
        return self.repo.get_by_key(key)

    def get_by_group(self, group: str):
        return self.repo.get_by_group(group)

    def get_groups(self):
        return self.repo.get_groups()

    def get_grouped_settings(self) -> dict:
        groups = self.get_groups()
        result = {}
        for group in groups:
            settings = self.get_by_group(group)
            if settings:
                result[group] = settings
        return result

    def get_value(self, key: str, default=None):
        return self.repo.get_value(key, default)

    def create(self, **kwargs) -> dict:
        try:
            setting = self.repo.create(**kwargs)
            return {'success': True, 'data': setting}
        except Exception as e:
            logger.exception("Failed to create setting")
            return {'success': False, 'error': str(e)}

    def update(self, setting_id: int, **kwargs) -> dict:
        try:
            setting = self.repo.update(setting_id, **kwargs)
            if setting:
                return {'success': True, 'data': setting}
            return {'success': False, 'error': 'Setting not found'}
        except Exception as e:
            logger.exception("Failed to update setting")
            return {'success': False, 'error': str(e)}

    def update_by_key(self, key: str, value: str) -> dict:
        try:
            setting = self.repo.update_by_key(key, value)
            if setting:
                return {'success': True, 'data': setting}
            return {'success': False, 'error': 'Setting not found'}
        except Exception as e:
            logger.exception("Failed to update setting by key")
            return {'success': False, 'error': str(e)}

    def bulk_update(self, settings_dict: dict[str, str]) -> dict:
        try:
            count = self.repo.bulk_update(settings_dict)
            return {'success': True, 'count': count}
        except Exception as e:
            logger.exception("Failed to bulk update settings")
            return {'success': False, 'error': str(e)}

    def delete(self, setting_id: int) -> dict:
        try:
            if self.repo.delete(setting_id):
                return {'success': True, 'message': 'Setting deleted successfully'}
            return {'success': False, 'error': 'Setting not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
