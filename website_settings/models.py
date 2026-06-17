from django.db import models


class SiteSetting(models.Model):
    SETTING_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('textarea', 'Textarea'),
        ('color', 'Color'),
        ('email', 'Email'),
        ('url', 'URL'),
        ('phone', 'Phone'),
    )
    GROUP_CHOICES = (
        ('general', 'General'),
        ('branding', 'Branding'),
        ('contact', 'Contact'),
        ('social', 'Social Media'),
        ('background', 'Background'),
        ('footer', 'Footer'),
        ('seo', 'SEO'),
        ('custom', 'Custom'),
    )
    key = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=200)
    value = models.TextField(blank=True)
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='text')
    group = models.CharField(max_length=20, choices=GROUP_CHOICES, default='general')
    order = models.IntegerField(default=0)
    is_public = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['group', 'order']

    def __str__(self):
        return self.label
