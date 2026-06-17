from django.db import models


class AnalyticsCache(models.Model):
    key = models.CharField(max_length=200, unique=True)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name_plural = 'Analytics Caches'

    def __str__(self):
        return self.key


class UserActivity(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    metadata = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user} - {self.action}"
