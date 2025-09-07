from django import forms
from .models import Job, Application, Profile
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class JobSearchForm(forms.Form):
    q = forms.CharField(required=False, label='Keyword')
    location = forms.CharField(required=False)

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'company', 'description', 'location']

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['resume', 'cover_letter']

class SignupForm(UserCreationForm):
    ROLE_CHOICES = (('applicant','Applicant'), ('employer','Employer'))
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role')

    def save(self, commit=True):
        user = super().save(commit=commit)
        # profile will be created by signal; set role here if possible
        return user
