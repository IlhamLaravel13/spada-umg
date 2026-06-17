from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Role, UserSession, LoginAttempt
from .services import AuthService, UserService, SessionService
from .repositories import UserRepository, SessionRepository

User = get_user_model()


class RoleModelTest(TestCase):
    def setUp(self):
        self.role = Role.objects.create(
            name='Mahasiswa', slug='mahasiswa',
            description='Student role'
        )

    def test_role_creation(self):
        self.assertEqual(self.role.name, 'Mahasiswa')
        self.assertEqual(self.role.slug, 'mahasiswa')
        self.assertTrue(self.role.is_active)

    def test_role_str(self):
        self.assertEqual(str(self.role), 'Mahasiswa')


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@umg.ac.id',
            password='testpass123',
            role='mahasiswa',
            nim='2024001',
        )

    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.role, 'mahasiswa')
        self.assertEqual(self.user.nim, '2024001')
        self.assertTrue(self.user.is_mahasiswa())
        self.assertFalse(self.user.is_dosen())
        self.assertFalse(self.user.is_admin())

    def test_user_str(self):
        expected = f"testuser (Mahasiswa)"
        self.assertEqual(str(self.user), expected)

    def test_is_admin(self):
        admin_user = User.objects.create_superuser(
            username='admin', email='admin@umg.ac.id', password='admin123'
        )
        admin_user.role = 'superadmin'
        admin_user.save()
        self.assertTrue(admin_user.is_admin())


class LoginFormTest(TestCase):
    def setUp(self):
        User.objects.create_user(
            username='mahasiswa1',
            email='mhs@umg.ac.id',
            password='password123',
            nim='2024001',
            role='mahasiswa',
        )

    def test_login_with_nim(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': '2024001',
            'password': 'password123',
        })
        self.assertIn(response.status_code, [200, 302])


class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@umg.ac.id',
            password='testpass123',
            role='mahasiswa',
            nim='2024001',
        )

    def test_login_view_get(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_login_view_post_success(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)

    def test_login_view_post_failure(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)

    def test_register_mahasiswa_view_get(self):
        response = self.client.get(reverse('accounts:register_mahasiswa'))
        self.assertEqual(response.status_code, 200)

    def test_profile_view_requires_login(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)

    def test_profile_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)

    def test_logout_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)

    def test_password_change_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:password_change'))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_view(self):
        response = self.client.get(reverse('accounts:password_reset'))
        self.assertEqual(response.status_code, 200)


class AuthServiceTest(TestCase):
    def setUp(self):
        self.auth_service = AuthService()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@umg.ac.id',
            password='testpass123',
            role='mahasiswa',
            nim='2024001',
        )

    def test_authenticate_with_username(self):
        result = self.auth_service.authenticate_user(
            'testuser', 'testpass123'
        )
        self.assertTrue(result['success'])

    def test_authenticate_with_nim(self):
        result = self.auth_service.authenticate_user(
            '2024001', 'testpass123'
        )
        self.assertTrue(result['success'])

    def test_authenticate_with_email(self):
        result = self.auth_service.authenticate_user(
            'test@umg.ac.id', 'testpass123'
        )
        self.assertTrue(result['success'])

    def test_authenticate_wrong_password(self):
        result = self.auth_service.authenticate_user(
            'testuser', 'wrongpassword'
        )
        self.assertFalse(result['success'])
        self.assertIn('Password salah', result['error'])

    def test_authenticate_nonexistent_user(self):
        result = self.auth_service.authenticate_user(
            'nonexistent', 'password123'
        )
        self.assertFalse(result['success'])
        self.assertIn('tidak ditemukan', result['error'])

    def test_register_mahasiswa(self):
        result = self.auth_service.register_mahasiswa(
            username='newstudent',
            email='student@umg.ac.id',
            password='password123',
            nim='2024002',
            first_name='New',
            last_name='Student',
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['user'].role, 'mahasiswa')

    def test_register_mahasiswa_duplicate_username(self):
        result = self.auth_service.register_mahasiswa(
            username='testuser',
            email='other@umg.ac.id',
            password='password123',
            nim='2024002',
        )
        self.assertFalse(result['success'])


class RepositoriesTest(TestCase):
    def setUp(self):
        self.user_repo = UserRepository()
        self.session_repo = SessionRepository()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@umg.ac.id',
            password='testpass123',
            role='mahasiswa',
            nim='2024001',
        )

    def test_get_by_username(self):
        user = self.user_repo.get_by_username('testuser')
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'test@umg.ac.id')

    def test_get_by_nim(self):
        user = self.user_repo.get_by_nim('2024001')
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser')

    def test_get_by_login_identifier_with_email(self):
        user = self.user_repo.get_by_login_identifier('test@umg.ac.id')
        self.assertIsNotNone(user)

    def test_get_by_login_identifier_with_nim(self):
        user = self.user_repo.get_by_login_identifier('2024001')
        self.assertIsNotNone(user)

    def test_get_active_users(self):
        qs = self.user_repo.get_active_users()
        self.assertTrue(qs.filter(id=self.user.id).exists())

    def test_get_users_by_role(self):
        qs = self.user_repo.get_users_by_role('mahasiswa')
        self.assertTrue(qs.filter(id=self.user.id).exists())


class URLTest(TestCase):
    def test_login_url(self):
        self.assertEqual(reverse('accounts:login'), '/accounts/login/')

    def test_register_url(self):
        self.assertEqual(reverse('accounts:register'), '/accounts/register/')

    def test_register_mahasiswa_url(self):
        self.assertEqual(
            reverse('accounts:register_mahasiswa'),
            '/accounts/register/mahasiswa/'
        )

    def test_register_dosen_url(self):
        self.assertEqual(
            reverse('accounts:register_dosen'),
            '/accounts/register/dosen/'
        )

    def test_profile_url(self):
        self.assertEqual(reverse('accounts:profile'), '/accounts/profile/')

    def test_password_reset_url(self):
        self.assertEqual(
            reverse('accounts:password_reset'),
            '/accounts/password-reset/'
        )
