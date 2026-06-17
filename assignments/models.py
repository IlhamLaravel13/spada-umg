from django.db import models
from django.utils import timezone


class Assignment(models.Model):
    class_meta = models.ForeignKey('academics.Class', on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    max_score = models.IntegerField(default=100)
    passing_score = models.IntegerField(default=60)
    due_date = models.DateTimeField()
    allow_late_submission = models.BooleanField(default=False)
    late_penalty_percent = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=1)
    is_published = models.BooleanField(default=True)
    is_group_assignment = models.BooleanField(default=False)
    file_required = models.BooleanField(default=True)
    allowed_file_types = models.CharField(max_length=500, blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-due_date', 'title']

    def __str__(self):
        return self.title

    def is_past_due(self):
        return timezone.now() > self.due_date

    def is_late(self):
        return self.is_past_due() and self.allow_late_submission


class AssignmentSubmission(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('late', 'Late'),
        ('resubmitted', 'Resubmitted'),
    ]
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    file = models.FileField(upload_to='submissions/', blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL, related_name='graded_submissions')
    attempt_number = models.IntegerField(default=1)
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['assignment', 'student', 'attempt_number']

    def __str__(self):
        return f"{self.student} - {self.assignment} (Attempt {self.attempt_number})"


class AssignmentSubmissionAttachment(models.Model):
    submission = models.ForeignKey(AssignmentSubmission, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='submissions/attachments/')
    original_name = models.CharField(max_length=255)
    file_size = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return self.original_name
