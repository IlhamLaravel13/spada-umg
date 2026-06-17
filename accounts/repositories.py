from django.db.models import QuerySet, Q
from django.utils import timezone
from .models import User, Role, UserSession, LoginAttempt


class UserRepository:
    def get_by_id(self, user_id: int) -> User | None:
        return User.objects.filter(id=user_id).first()

    def get_by_username(self, username: str) -> User | None:
        return User.objects.filter(username=username).first()

    def get_by_email(self, email: str) -> User | None:
        return User.objects.filter(email=email).first()

    def get_by_nim(self, nim: str) -> User | None:
        return User.objects.filter(nim=nim).first()

    def get_by_nidn(self, nidn: str) -> User | None:
        return User.objects.filter(nidn=nidn).first()

    def get_by_nip(self, nip: str) -> User | None:
        return User.objects.filter(nip=nip).first()

    def get_by_login_identifier(self, identifier: str) -> User | None:
        return User.objects.filter(
            Q(username=identifier) |
            Q(email=identifier) |
            Q(nim=identifier) |
            Q(nidn=identifier) |
            Q(nip=identifier)
        ).first()

    def get_active_users(self) -> QuerySet[User]:
        return User.objects.filter(is_active=True)

    def get_users_by_role(self, role: str) -> QuerySet[User]:
        return User.objects.filter(role=role, is_active=True)

    def get_verified_users(self) -> QuerySet[User]:
        return User.objects.filter(is_verified=True)

    def get_recently_joined(self, days: int = 30) -> QuerySet[User]:
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return User.objects.filter(date_joined__gte=cutoff)

    def search(self, query: str) -> QuerySet[User]:
        return User.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(nim__icontains=query) |
            Q(nidn__icontains=query) |
            Q(nip__icontains=query) |
            Q(phone__icontains=query)
        )

    def create_user(self, **kwargs) -> User:
        return User.objects.create_user(**kwargs)

    def update_user(self, user_id: int, **kwargs) -> User | None:
        updated = User.objects.filter(id=user_id).update(**kwargs)
        if updated:
            return self.get_by_id(user_id)
        return None

    def deactivate_user(self, user_id: int) -> bool:
        return User.objects.filter(id=user_id).update(
            is_active=False, updated_at=timezone.now()
        ) > 0

    def activate_user(self, user_id: int) -> bool:
        return User.objects.filter(id=user_id).update(
            is_active=True, updated_at=timezone.now()
        ) > 0

    def verify_email(self, user_id: int) -> bool:
        return User.objects.filter(id=user_id).update(
            is_verified=True, email_verified_at=timezone.now(),
            updated_at=timezone.now()
        ) > 0

    def update_last_activity(self, user_id: int) -> bool:
        return User.objects.filter(id=user_id).update(
            last_activity=timezone.now()
        ) > 0

    def count_active_users(self) -> int:
        return User.objects.filter(is_active=True).count()

    def count_by_role(self) -> dict:
        return {
            role: User.objects.filter(role=role).count()
            for role, _ in User.ROLE_CHOICES
        }


class RoleRepository:
    def get_all(self) -> QuerySet[Role]:
        return Role.objects.filter(is_active=True)

    def get_by_slug(self, slug: str) -> Role | None:
        return Role.objects.filter(slug=slug).first()

    def get_by_name(self, name: str) -> Role | None:
        return Role.objects.filter(name=name).first()

    def create_role(self, name: str, description: str = '') -> Role:
        return Role.objects.create(name=name, description=description)

    def deactivate_role(self, role_id: int) -> bool:
        return Role.objects.filter(id=role_id).update(is_active=False) > 0


class SessionRepository:
    def get_user_sessions(self, user_id: int) -> QuerySet[UserSession]:
        return UserSession.objects.filter(user_id=user_id).order_by('-last_activity')

    def get_active_sessions(self, user_id: int) -> QuerySet[UserSession]:
        return UserSession.objects.filter(user_id=user_id, is_active=True)

    def create_session(self, user_id: int, session_key: str, ip_address: str = None,
                       user_agent: str = '') -> UserSession:
        return UserSession.objects.create(
            user_id=user_id, session_key=session_key,
            ip_address=ip_address, user_agent=user_agent
        )

    def deactivate_session(self, session_id: int) -> bool:
        return UserSession.objects.filter(id=session_id).update(is_active=False) > 0

    def deactivate_all_user_sessions(self, user_id: int, exclude_session_key: str = None) -> int:
        qs = UserSession.objects.filter(user_id=user_id, is_active=True)
        if exclude_session_key:
            qs = qs.exclude(session_key=exclude_session_key)
        return qs.update(is_active=False)

    def record_login_attempt(self, username: str, ip_address: str,
                            user_agent: str = '', was_successful: bool = False) -> LoginAttempt:
        return LoginAttempt.objects.create(
            username=username, ip_address=ip_address,
            user_agent=user_agent, was_successful=was_successful
        )

    def get_recent_login_attempts(self, username: str, minutes: int = 15) -> QuerySet[LoginAttempt]:
        cutoff = timezone.now() - timezone.timedelta(minutes=minutes)
        return LoginAttempt.objects.filter(
            username=username, attempted_at__gte=cutoff
        ).order_by('-attempted_at')

    def count_failed_attempts(self, username: str, minutes: int = 15) -> int:
        cutoff = timezone.now() - timezone.timedelta(minutes=minutes)
        return LoginAttempt.objects.filter(
            username=username, was_successful=False, attempted_at__gte=cutoff
        ).count()
