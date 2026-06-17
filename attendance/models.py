from django.db import models
from django.utils import timezone

class AttendanceSession(models.Model):
    class_meta = models.ForeignKey('academics.Class', on_delete=models.CASCADE, related_name='attendance_sessions')
    title = models.CharField(max_length=200)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    topic = models.CharField(max_length=200, blank=True)
    meeting_number = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    qr_code = models.ImageField(upload_to='attendance/qrcodes/', blank=True)
    qr_code_secret = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-start_time']
    
    def __str__(self):
        return f"{self.class_meta} - {self.date}"

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Hadir'),
        ('late', 'Terlambat'),
        ('absent', 'Tidak Hadir'),
        ('excused', 'Izin'),
        ('sick', 'Sakit'),
    )
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='attendances')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    check_in_time = models.DateTimeField(auto_now_add=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True)
    verified_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_attendances')
    
    class Meta:
        ordering = ['-session__date']
        unique_together = ['session', 'student']
    
    def __str__(self):
        return f"{self.student} - {self.session} - {self.get_status_display()}"
