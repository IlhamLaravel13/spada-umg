from django.db import models


class LibraryCategory(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='book')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Library Categories'

    def __str__(self):
        return self.name


class LibraryItem(models.Model):
    TYPE_CHOICES = (
        ('ebook', 'E-Book'),
        ('journal', 'Jurnal'),
        ('module', 'Modul'),
        ('thesis', 'Skripsi'),
        ('final_project', 'Tugas Akhir'),
        ('paper', 'Paper'),
        ('proceeding', 'Prosiding'),
        ('other', 'Lainnya'),
    )
    title = models.CharField(max_length=300)
    author = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    category = models.ForeignKey(LibraryCategory, on_delete=models.SET_NULL, null=True, blank=True)
    faculty = models.ForeignKey('academics.Faculty', on_delete=models.SET_NULL, null=True, blank=True)
    study_program = models.ForeignKey('academics.StudyProgram', on_delete=models.SET_NULL, null=True, blank=True)
    file = models.FileField(upload_to='library/')
    cover_image = models.ImageField(upload_to='library/covers/', blank=True)
    publisher = models.CharField(max_length=200, blank=True)
    publication_year = models.IntegerField(null=True, blank=True)
    isbn = models.CharField(max_length=20, blank=True)
    pages = models.IntegerField(null=True, blank=True)
    language = models.CharField(max_length=50, default='Indonesia')
    tags = models.CharField(max_length=500, blank=True)
    download_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    is_published = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Library Items'

    def __str__(self):
        return self.title
