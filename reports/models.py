from django.db import models

class Report(models.Model):
    TYPE_CHOICES = (
        ('academic', 'Academic Report'),
        ('attendance', 'Attendance Report'),
        ('grade', 'Grade Report'),
        ('payment', 'Payment Report'),
        ('user', 'User Report'),
        ('course', 'Course Report'),
    )
    FORMAT_CHOICES = (('pdf', 'PDF'), ('excel', 'Excel'), ('csv', 'CSV'))
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    parameters = models.JSONField(default=dict)
    generated_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    file = models.FileField(upload_to='reports/', blank=True)
    is_ready = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
