from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from .models import Job, Application, Profile
from .forms import JobForm, ApplicationForm, JobSearchForm, SignupForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.views import LogoutView

# Utility mixin to ensure user is employer
class EmployerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'profile') and self.request.user.profile.role == 'employer'

class ApplicantRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'profile') and self.request.user.profile.role == 'applicant'

# Home page
class HomeView(TemplateView):
    template_name = 'jobs/home.html'

# Job list with pagination and filtering
class JobListView(ListView):
    model = Job
    template_name = 'jobs/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q', '')
        location = self.request.GET.get('location', '')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(company__icontains=q))
        if location:
            qs = qs.filter(location__icontains=location)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['search_form'] = JobSearchForm(self.request.GET)
        return ctx

class JobDetailView(DetailView):
    model = Job
    template_name = 'jobs/job_detail.html'
    context_object_name = 'job'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        job = self.get_object()
        ctx['applications'] = job.applications.all() if self.request.user == job.posted_by else None
        ctx['application_form'] = ApplicationForm()
        return ctx

# Job create (Employer)
class JobCreateView(LoginRequiredMixin, EmployerRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/job_form.html'

    def form_valid(self, form):
        form.instance.posted_by = self.request.user
        return super().form_valid(form)

# Job update (only poster)
class JobUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/job_form.html'

    def test_func(self):
        job = self.get_object()
        return self.request.user == job.posted_by

# Job delete
class JobDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Job
    template_name = 'jobs/job_confirm_delete.html'
    success_url = reverse_lazy('jobs:job_list')

    def test_func(self):
        job = self.get_object()
        return self.request.user == job.posted_by

# Apply to job (ModelForm)
class ApplyView(LoginRequiredMixin, ApplicantRequiredMixin, CreateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'jobs/application_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.job = get_object_or_404(Job, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # enforce uniqueness - handled by unique_together, but better UX here:
        if Application.objects.filter(job=self.job, applicant=self.request.user).exists():
            form.add_error(None, 'You have already applied to this job.')
            return self.form_invalid(form)
        form.instance.job = self.job
        form.instance.applicant = self.request.user
        resp = super().form_valid(form)

        # send confirmation email
        try:
            subject = f"Application received for {self.job.title}"
            message = f"Hi {self.request.user.username},\n\nWe've received your application for '{self.job.title}' at {self.job.company}.\n\nRegards,\n{settings.DEFAULT_FROM_EMAIL}"
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [self.request.user.email], fail_silently=False)
        except Exception:
            # in production, log the exception
            pass

        messages.success(self.request, 'Application submitted successfully.')
        return resp

    def get_success_url(self):
        return reverse_lazy('jobs:job_detail', kwargs={'pk': self.job.pk})

# Withdraw application
from django.views import View
class WithdrawApplicationView(LoginRequiredMixin, View):
    def post(self, request, pk):
        app = get_object_or_404(Application, pk=pk, applicant=request.user)
        app.status = 'withdrawn'
        app.save()
        messages.success(request, 'Application withdrawn.')
        return redirect('jobs:my_applications')

# Applicant dashboard - list own applications
class MyApplicationsView(LoginRequiredMixin, ApplicantRequiredMixin, ListView):
    template_name = 'jobs/my_applications.html'
    context_object_name = 'applications'
    paginate_by = 20

    def get_queryset(self):
        return Application.objects.filter(applicant=self.request.user).order_by('-applied_at')

# Employer dashboard - list posted jobs and applications
class EmployerDashboardView(LoginRequiredMixin, EmployerRequiredMixin, TemplateView):
    template_name = 'jobs/employer_dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['jobs'] = Job.objects.filter(posted_by=self.request.user)
        return ctx

# Signup view
class SignupView(FormView):
    template_name = 'jobs/signup.html'
    form_class = SignupForm
    success_url = reverse_lazy('jobs:home')

    def form_valid(self, form):
        user = form.save()
        # set role on profile if provided
        role = form.cleaned_data.get('role')
        user.profile.role = role
        if role == 'employer':
            user.profile.company = self.request.POST.get('company', '') or ''
        user.profile.save()

        # log user in
        login(self.request, user)
        return super().form_valid(form)

# ------------------ Login / Logout ------------------
class UserLoginView(LoginView):
    template_name = 'jobs/login.html'

    def get_success_url(self):
        return reverse_lazy('jobs:home')


class UserLogoutView(LogoutView):
    next_page = reverse_lazy('jobs:home')

class CustomLogoutView(LogoutView):
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)