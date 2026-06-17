from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.db import transaction
from .repositories import UserRepository, SessionRepository
from .models import User


MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.session_repo = SessionRepository()

    def authenticate_user(self, identifier: str, password: str,
                          ip_address: str = None, user_agent: str = '',
                          request=None) -> dict:
        user = self.user_repo.get_by_login_identifier(identifier)

        if not user:
            self.session_repo.record_login_attempt(
                identifier, ip_address or '', user_agent, False
            )
            return {'success': False, 'error': 'User tidak ditemukan'}

        failed_attempts = self.session_repo.count_failed_attempts(
            user.username, LOCKOUT_MINUTES
        )
        if failed_attempts >= MAX_LOGIN_ATTEMPTS:
            return {
                'success': False,
                'error': f'Akun terkunci sementara. Silakan coba lagi dalam {LOCKOUT_MINUTES} menit.'
            }

        credentials = {'password': password}
        if '@' in identifier and '.' in identifier:
            credentials['email'] = identifier
        else:
            credentials['username'] = identifier

        auth_user = authenticate(request=request, **credentials)

        if auth_user is None:
            self.session_repo.record_login_attempt(
                user.username, ip_address or '', user_agent, False
            )
            remaining = MAX_LOGIN_ATTEMPTS - failed_attempts - 1
            return {'success': False, 'error': f'Password salah. Sisa percobaan: {remaining}'}

        if not auth_user.is_active:
            return {'success': False, 'error': 'Akun tidak aktif. Hubungi administrator.'}

        self.session_repo.record_login_attempt(
            auth_user.username, ip_address or '', user_agent, True
        )
        self.user_repo.update_last_activity(auth_user.id)

        if request:
            login(request, auth_user)
            self._manage_session(request, auth_user, ip_address, user_agent)

        return {'success': True, 'user': auth_user}

    def _manage_session(self, request, user, ip_address, user_agent):
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        self.session_repo.create_session(
            user.id, session_key, ip_address, user_agent
        )

    def register_mahasiswa(self, username: str, email: str, password: str,
                           nim: str, first_name: str = '', last_name: str = '',
                           phone: str = '', **extra_fields) -> dict:
        if self.user_repo.get_by_username(username):
            return {'success': False, 'error': 'Username sudah digunakan'}
        if self.user_repo.get_by_email(email):
            return {'success': False, 'error': 'Email sudah terdaftar'}
        if self.user_repo.get_by_nim(nim):
            return {'success': False, 'error': 'NIM sudah terdaftar'}

        try:
            with transaction.atomic():
                user = self.user_repo.create_user(
                    username=username,
                    email=email,
                    password=password,
                    nim=nim,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    role='mahasiswa',
                    **extra_fields
                )
            return {'success': True, 'user': user}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def register_dosen(self, username: str, email: str, password: str,
                       nidn: str = '', nip: str = '', first_name: str = '',
                       last_name: str = '', phone: str = '', **extra_fields) -> dict:
        if self.user_repo.get_by_username(username):
            return {'success': False, 'error': 'Username sudah digunakan'}
        if self.user_repo.get_by_email(email):
            return {'success': False, 'error': 'Email sudah terdaftar'}
        if nidn and self.user_repo.get_by_nidn(nidn):
            return {'success': False, 'error': 'NIDN sudah terdaftar'}
        if nip and self.user_repo.get_by_nip(nip):
            return {'success': False, 'error': 'NIP sudah terdaftar'}

        try:
            with transaction.atomic():
                user = self.user_repo.create_user(
                    username=username,
                    email=email,
                    password=password,
                    nidn=nidn or None,
                    nip=nip or None,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    role='dosen',
                    **extra_fields
                )
            return {'success': True, 'user': user}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def verify_email_token(self, user_id: int) -> dict:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {'success': False, 'error': 'User tidak ditemukan'}
        if user.is_verified:
            return {'success': False, 'error': 'Email sudah terverifikasi'}
        self.user_repo.verify_email(user_id)
        return {'success': True, 'message': 'Email berhasil diverifikasi'}

    def logout_user(self, request):
        session_key = request.session.session_key
        if session_key and request.user.is_authenticated:
            sessions = self.session_repo.get_active_sessions(request.user.id)
            for s in sessions:
                if s.session_key == session_key:
                    self.session_repo.deactivate_session(s.id)
        logout(request)


class UserService:
    def __init__(self):
        self.user_repo = UserRepository()

    def get_user_profile(self, user_id: int) -> User | None:
        return self.user_repo.get_by_id(user_id)

    def update_profile(self, user_id: int, **kwargs) -> dict:
        allowed_fields = [
            'first_name', 'last_name', 'phone', 'bio', 'avatar',
            'faculty', 'study_program', 'theme_preference',
            'email_notifications', 'enrollment_year'
        ]
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
        if update_data:
            user = self.user_repo.update_user(user_id, **update_data)
            if user:
                return {'success': True, 'user': user}
        return {'success': False, 'error': 'Tidak ada data yang diupdate'}

    def change_password(self, user: User, old_password: str,
                        new_password: str) -> dict:
        if not user.check_password(old_password):
            return {'success': False, 'error': 'Password saat ini salah'}
        if old_password == new_password:
            return {'success': False, 'error': 'Password baru harus berbeda dari password lama'}
        user.set_password(new_password)
        user.save(update_fields=['password'])
        return {'success': True, 'message': 'Password berhasil diubah'}

    def deactivate_account(self, user_id: int) -> dict:
        result = self.user_repo.deactivate_user(user_id)
        if result:
            return {'success': True, 'message': 'Akun berhasil dinonaktifkan'}
        return {'success': False, 'error': 'Gagal menonaktifkan akun'}

    def get_users_by_role(self, role: str):
        return self.user_repo.get_users_by_role(role)


class SessionService:
    def __init__(self):
        self.session_repo = SessionRepository()

    def get_active_sessions(self, user_id: int):
        return self.session_repo.get_active_sessions(user_id)

    def terminate_session(self, session_id: int, user_id: int) -> dict:
        session = self.session_repo.get_active_sessions(user_id).filter(id=session_id).first()
        if not session:
            return {'success': False, 'error': 'Sesi tidak ditemukan'}
        self.session_repo.deactivate_session(session_id)
        return {'success': True, 'message': 'Sesi berhasil diakhiri'}

    def terminate_all_sessions(self, user_id: int, exclude_key: str = None) -> dict:
        count = self.session_repo.deactivate_all_user_sessions(user_id, exclude_key)
        return {'success': True, 'message': f'{count} sesi berhasil diakhiri'}
