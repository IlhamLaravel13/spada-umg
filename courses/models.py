from django.db import models


class Material(models.Model):
    TYPE_CHOICES = (
        ('pdf', 'PDF'),
        ('docx', 'DOCX'),
        ('pptx', 'PPTX'),
        ('xlsx', 'XLSX'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('image', 'Image'),
        ('archive', 'Archive'),
        ('link', 'Link'),
        ('other', 'Other'),
    )
    class_meta = models.ForeignKey('academics.Class', on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    file = models.FileField(upload_to='materials/', blank=True)
    file_url = models.URLField(blank=True)
    file_size = models.IntegerField(default=0)
    is_published = models.BooleanField(default=True)
    allow_download = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    uploaded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title


class MaterialComment(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user} - {self.material}"


class CourseProgress(models.Model):
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    class_meta = models.ForeignKey('academics.Class', on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE, null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['student', 'material']

    def __str__(self):
        return f"{self.student} - {self.material} - {'Done' if self.is_completed else 'Pending'}"
