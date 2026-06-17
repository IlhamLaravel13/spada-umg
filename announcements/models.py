from django.db import models

class Announcement(models.Model):
    CATEGORY_CHOICES = (
        ('kelas_libur', 'Kelas Libur'),
        ('perubahan_jadwal', 'Perubahan Jadwal'),
        ('penggantian_ruangan', 'Penggantian Ruangan'),
        ('informasi_uts', 'Informasi UTS'),
        ('informasi_uas', 'Informasi UAS'),
        ('informasi_akademik', 'Informasi Akademik'),
        ('berita', 'Berita'),
        ('umum', 'Umum'),
    )
    AUDIENCE_CHOICES = (
        ('all', 'Semua'),
        ('mahasiswa', 'Mahasiswa'),
        ('dosen', 'Dosen'),
        ('admin', 'Admin'),
        ('class', 'Per Kelas'),
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='umum')
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default='all')
    target_class = models.ForeignKey('academics.Class', on_delete=models.SET_NULL, null=True, blank=True)
    is_important = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    attachment = models.FileField(upload_to='announcements/', blank=True)
    pinned_until = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_important', '-created_at']
    
    def __str__(self):
        return self.title

class AnnouncementRead(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='reads')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['announcement', 'user']
