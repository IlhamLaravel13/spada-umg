from django.db.models import QuerySet
from .models import SiteSetting


class SiteSettingRepository:
    def get_all(self) -> QuerySet[SiteSetting]:
        return SiteSetting.objects.all()

    def get_by_id(self, setting_id: int) -> SiteSetting | None:
        return SiteSetting.objects.filter(id=setting_id).first()

    def get_by_key(self, key: str) -> SiteSetting | None:
        return SiteSetting.objects.filter(key=key).first()

    def get_by_group(self, group: str) -> QuerySet[SiteSetting]:
        return SiteSetting.objects.filter(group=group).order_by('order')

    def get_groups(self) -> list:
        return SiteSetting.objects.values_list('group', flat=True).distinct().order_by('group')

    def get_public(self) -> QuerySet[SiteSetting]:
        return SiteSetting.objects.filter(is_public=True)

    def get_public_by_group(self, group: str) -> QuerySet[SiteSetting]:
        return SiteSetting.objects.filter(is_public=True, group=group).order_by('order')

    def get_value(self, key: str, default=None) -> str | None:
        setting = self.get_by_key(key)
        return setting.value if setting else default

    def create(self, **kwargs) -> SiteSetting:
        return SiteSetting.objects.create(**kwargs)

    def update(self, setting_id: int, **kwargs) -> SiteSetting | None:
        updated = SiteSetting.objects.filter(id=setting_id).update(**kwargs)
        if updated:
            return self.get_by_id(setting_id)
        return None

    def update_by_key(self, key: str, value: str) -> SiteSetting | None:
        updated = SiteSetting.objects.filter(key=key).update(value=value)
        if updated:
            return self.get_by_key(key)
        return None

    def bulk_update(self, settings_dict: dict[str, str]) -> int:
        count = 0
        for key, value in settings_dict.items():
            updated = SiteSetting.objects.filter(key=key).update(value=value)
            if updated:
                count += 1
        return count

    def delete(self, setting_id: int) -> bool:
        return SiteSetting.objects.filter(id=setting_id).delete()[0] > 0
