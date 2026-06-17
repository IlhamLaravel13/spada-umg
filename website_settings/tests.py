from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import SiteSetting

User = get_user_model()


class BaseSiteSettingTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin1', password='test123', role='admin',
            first_name='Admin', last_name='Satu',
        )
        self.dosen = User.objects.create_user(
            username='dosen1', password='test123', role='dosen',
            first_name='Dosen', last_name='Satu',
        )
        self.setting = SiteSetting.objects.create(
            key='site_name',
            label='Nama Situs',
            value='SPADA UMG',
            setting_type='text',
            group='general',
            order=1,
            is_public=True,
            description='Nama dari platform SPADA UMG',
        )
        self.contact_setting = SiteSetting.objects.create(
            key='contact_email',
            label='Email Kontak',
            value='info@umg.ac.id',
            setting_type='email',
            group='contact',
            order=1,
            is_public=True,
        )


class SiteSettingModelTest(BaseSiteSettingTest):
    def test_create_setting(self):
        self.assertEqual(self.setting.key, 'site_name')
        self.assertEqual(str(self.setting), 'Nama Situs')
        self.assertTrue(self.setting.is_public)

    def test_setting_ordering(self):
        s2 = SiteSetting.objects.create(
            key='test_key', label='Test', value='val',
            setting_type='text', group='general', order=2,
        )
        qs = SiteSetting.objects.filter(group='general')
        self.assertEqual(qs.first(), self.setting)

    def test_group_choices(self):
        self.assertIn(self.setting.group, dict(SiteSetting.GROUP_CHOICES))

    def test_setting_type_choices(self):
        self.assertIn(self.setting.setting_type, dict(SiteSetting.SETTING_TYPES))


class SiteSettingViewsTest(BaseSiteSettingTest):
    def test_settings_list_requires_admin(self):
        response = self.client.get(reverse('website_settings:settings_list'))
        self.assertNotEqual(response.status_code, 200)

    def test_settings_list_admin(self):
        self.client.login(username='admin1', password='test123')
        response = self.client.get(reverse('website_settings:settings_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'website_settings/settings_list.html')

    def test_settings_list_non_admin(self):
        self.client.login(username='dosen1', password='test123')
        response = self.client.get(reverse('website_settings:settings_list'))
        self.assertNotEqual(response.status_code, 200)

    def test_bulk_update(self):
        self.client.login(username='admin1', password='test123')
        response = self.client.post(reverse('website_settings:settings_bulk_update'), {
            'setting_site_name': 'SPADA UMG Updated',
            'setting_contact_email': 'admin@umg.ac.id',
        })
        self.assertIn(response.status_code, [200, 302])
        self.setting.refresh_from_db()
        self.assertEqual(self.setting.value, 'SPADA UMG Updated')

    def test_setting_create(self):
        self.client.login(username='admin1', password='test123')
        response = self.client.post(reverse('website_settings:setting_create'), {
            'key': 'new_setting',
            'label': 'New Setting',
            'value': 'value123',
            'setting_type': 'text',
            'group': 'custom',
            'order': 1,
        })
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(SiteSetting.objects.filter(key='new_setting').exists())

    def test_setting_update(self):
        self.client.login(username='admin1', password='test123')
        response = self.client.post(reverse('website_settings:setting_update', args=[self.setting.id]), {
            'key': 'site_name',
            'label': 'Nama Situs Updated',
            'value': 'SPADA UMG v2',
            'setting_type': 'text',
            'group': 'general',
            'order': 1,
        })
        self.assertIn(response.status_code, [200, 302])
        self.setting.refresh_from_db()
        self.assertEqual(self.setting.value, 'SPADA UMG v2')

    def test_setting_delete(self):
        self.client.login(username='admin1', password='test123')
        response = self.client.post(reverse('website_settings:setting_delete', args=[self.setting.id]))
        self.assertIn(response.status_code, [200, 302])
        self.assertFalse(SiteSetting.objects.filter(id=self.setting.id).exists())


class SiteSettingServiceTest(BaseSiteSettingTest):
    def test_service_get_value(self):
        from .services import SiteSettingService
        service = SiteSettingService()
        val = service.get_value('site_name')
        self.assertEqual(val, 'SPADA UMG')

    def test_service_get_default(self):
        from .services import SiteSettingService
        service = SiteSettingService()
        val = service.get_value('nonexistent', 'default_val')
        self.assertEqual(val, 'default_val')

    def test_service_create(self):
        from .services import SiteSettingService
        service = SiteSettingService()
        result = service.create(
            key='test_service', label='Test', value='val',
            setting_type='text', group='custom',
        )
        self.assertTrue(result['success'])
        self.assertIsNotNone(service.get_by_key('test_service'))

    def test_service_bulk_update(self):
        from .services import SiteSettingService
        service = SiteSettingService()
        result = service.bulk_update({'site_name': 'Bulk Updated', 'contact_email': 'bulk@umg.ac.id'})
        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 2)

    def test_service_delete(self):
        from .services import SiteSettingService
        service = SiteSettingService()
        result = service.delete(self.setting.id)
        self.assertTrue(result['success'])

    def test_get_grouped_settings(self):
        from .services import SiteSettingService
        service = SiteSettingService()
        grouped = service.get_grouped_settings()
        self.assertIn('general', grouped)
        self.assertIn('contact', grouped)
