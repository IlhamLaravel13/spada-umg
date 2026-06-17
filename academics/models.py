from django.db import models
from django.utils.text import slugify

class Faculty(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)
    dean = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='deaned_faculties')
    logo = models.ImageField(upload_to='faculties/', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Faculties'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class StudyProgram(models.Model):
    DEGREE_CHOICES = (
        ('d3', 'D3'),
        ('d4', 'D4'),
        ('s1', 'S1'),
        ('s2', 'S2'),
        ('s3', 'S3'),
        ('profesi', 'Profesi'),
    )
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='study_programs')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    degree = models.CharField(max_length=20, choices=DEGREE_CHOICES)
    description = models.TextField(blank=True)
    head = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_programs')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['faculty', 'name']
        verbose_name_plural = 'Study Programs'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.get_degree_display()})"

class AcademicYear(models.Model):
    year = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=False)
    start_date = models.DateField()
    end_date = models.DateField()
    is_even_semester = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-year']
        verbose_name_plural = 'Academic Years'
    
    def __str__(self):
        return self.year

class Semester(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='semesters')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    is_active = models.BooleanField(default=False)
    start_date = models.DateField()
    end_date = models.DateField()
    midterm_start = models.DateField(null=True, blank=True)
    midterm_end = models.DateField(null=True, blank=True)
    finalterm_start = models.DateField(null=True, blank=True)
    finalterm_end = models.DateField(null=True, blank=True)
    enrollment_start = models.DateField(null=True, blank=True)
    enrollment_end = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-academic_year__year', 'name']
    
    def __str__(self):
        return f"{self.academic_year.year} - {self.name}"

class Course(models.Model):
    study_program = models.ForeignKey(StudyProgram, on_delete=models.CASCADE, related_name='courses')
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    credits = models.IntegerField(default=3)
    semester = models.IntegerField(help_text="Recommended semester number")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['code']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class Class(models.Model):
    CLASS_TYPE_CHOICES = (
        ('reguler', 'Reguler'),
        ('paralel', 'Paralel'),
        ('karyawan', 'Karyawan'),
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='classes')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='classes')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    lecturer = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='teaching_classes')
    co_lecturer = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='co_teaching_classes')
    class_type = models.CharField(max_length=20, choices=CLASS_TYPE_CHOICES, default='reguler')
    room = models.CharField(max_length=100, blank=True)
    schedule = models.CharField(max_length=200, blank=True)
    max_students = models.IntegerField(default=40)
    is_active = models.BooleanField(default=True)
    meeting_link = models.URLField(blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course__code', 'name']
        verbose_name_plural = 'Classes'
    
    def __str__(self):
        return f"{self.course.code} - {self.name} ({self.semester})"

class Enrollment(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
        ('failed', 'Failed'),
    )
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='enrollments')
    class_enrolled = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    enrollment_date = models.DateField(auto_now_add=True)
    grade_final = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grade_letter = models.CharField(max_length=2, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['class_enrolled__course__code']
        unique_together = ['student', 'class_enrolled']
    
    def __str__(self):
        return f"{self.student} - {self.class_enrolled}"
