from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
import os

def resume_upload_to(instance, filename):
    # store by user id and job id
    base, ext = os.path.splitext(filename)
    return f"resumes/user_{instance.applicant.id}/job_{instance.job.id}/{base}{ext}"

class Profile(models.Model):
    ROLE_CHOICES = (('employer', 'Employer'), ('applicant', 'Applicant'))
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='applicant')
    company = models.CharField(max_length=255, blank=True, null=True)  # optional for employer

    def __str__(self):
        return f"{self.user.username} ({self.role})"

class Job(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255, blank=True)
    posted_by = models.ForeignKey(User, related_name='jobs', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} @ {self.company}"

    def get_absolute_url(self):
        return reverse('jobs:job_detail', kwargs={'pk': self.pk})

def resume_file_validator(value):
    # validate extension and size
    from django.core.exceptions import ValidationError
    valid_exts = ['.pdf', '.doc', '.docx']
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in valid_exts:
        raise ValidationError('Unsupported file extension. Allowed: .pdf, .doc, .docx')
    if value.size > getattr(settings, 'MAX_UPLOAD_SIZE', 5 * 1024 * 1024):
        raise ValidationError(f'File too large. Max size is {settings.MAX_UPLOAD_SIZE} bytes.')

class Application(models.Model):
    STATUS_CHOICES = (
        ('applied', 'Applied'),
        ('under_review', 'Under Review'),
        ('rejected', 'Rejected'),
        ('accepted', 'Accepted'),
        ('withdrawn', 'Withdrawn'),
    )
    job = models.ForeignKey(Job, related_name='applications', on_delete=models.CASCADE)
    applicant = models.ForeignKey(User, related_name='applications', on_delete=models.CASCADE)
    resume = models.FileField(upload_to=resume_upload_to, validators=[resume_file_validator])
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'applicant')  # prevents duplicate applications

    def __str__(self):
        return f"Application by {self.applicant.username} for {self.job.title}"
