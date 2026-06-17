from django.db import models
from django.utils import timezone
from django.conf import settings


class ActivityLog(models.Model):
    ACTION_CHOICES = (
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('upload', 'Upload'),
        ('download', 'Download'),
        ('view', 'View'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action']),
        ]
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'

    def __str__(self):
        return f"{self.user or 'Anonymous'} - {self.action} - {self.model_name}"


class SystemConfig(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['key']
        verbose_name = 'System Config'
        verbose_name_plural = 'System Configs'

    def __str__(self):
        return self.key


class CampusBackground(models.Model):
    PAGE_CHOICES = (
        ('landing', 'Landing Page'),
        ('login', 'Login Page'),
        ('register', 'Register Page'),
        ('admin', 'Dashboard Admin'),
        ('dosen', 'Dashboard Dosen'),
        ('mahasiswa', 'Dashboard Mahasiswa'),
    )
    page = models.CharField(max_length=20, choices=PAGE_CHOICES, unique=True)
    image = models.ImageField(upload_to='backgrounds/')
    overlay_opacity = models.FloatField(default=0.35)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['page']
        verbose_name = 'Campus Background'
        verbose_name_plural = 'Campus Backgrounds'

    def __str__(self):
        return f"Background for {self.get_page_display()}"
