from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify
from django.utils import timezone


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('dosen', 'Dosen'),
        ('mahasiswa', 'Mahasiswa'),
        ('superadmin', 'Super Admin'),
    )
    THEME_CHOICES = (
        ('light', 'Light'),
        ('dark', 'Dark'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='mahasiswa')
    nim = models.CharField(max_length=20, unique=True, null=True, blank=True)
    nidn = models.CharField(max_length=20, unique=True, null=True, blank=True)
    nip = models.CharField(max_length=20, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    bio = models.TextField(blank=True)
    faculty = models.ForeignKey(
        'academics.Faculty', on_delete=models.SET_NULL, null=True, blank=True
    )
    study_program = models.ForeignKey(
        'academics.StudyProgram', on_delete=models.SET_NULL, null=True, blank=True
    )
    enrollment_year = models.IntegerField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    theme_preference = models.CharField(
        max_length=10, choices=THEME_CHOICES, default='light'
    )
    email_notifications = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_joined']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    def is_admin(self):
        return self.role in ['admin', 'superadmin']

    def is_dosen(self):
        return self.role == 'dosen'

    def is_mahasiswa(self):
        return self.role == 'mahasiswa'

    def get_login_identifier(self):
        if self.nim:
            return self.nim
        if self.nidn:
            return self.nidn
        if self.nip:
            return self.nip
        return self.email


class UserSession(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sessions'
    )
    session_key = models.CharField(max_length=40)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_activity']
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'

    def __str__(self):
        return f"{self.user.username} - {self.ip_address}"


class LoginAttempt(models.Model):
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    was_successful = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-attempted_at']
        verbose_name = 'Login Attempt'
        verbose_name_plural = 'Login Attempts'

    def __str__(self):
        return f"{self.username} - {'Success' if self.was_successful else 'Failed'} at {self.attempted_at}"
