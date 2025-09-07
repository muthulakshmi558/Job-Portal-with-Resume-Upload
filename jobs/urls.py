from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'jobs'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('jobs/', views.JobListView.as_view(), name='job_list'),
    path('jobs/<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('jobs/create/', views.JobCreateView.as_view(), name='job_create'),
    path('jobs/<int:pk>/edit/', views.JobUpdateView.as_view(), name='job_edit'),
    path('jobs/<int:pk>/delete/', views.JobDeleteView.as_view(), name='job_delete'),

    path('jobs/<int:pk>/apply/', views.ApplyView.as_view(), name='job_apply'),
    path('applications/<int:pk>/withdraw/', views.WithdrawApplicationView.as_view(), name='application_withdraw'),

    path('my-applications/', views.MyApplicationsView.as_view(), name='my_applications'),
    path('employer/dashboard/', views.EmployerDashboardView.as_view(), name='employer_dashboard'),

    path('signup/', views.SignupView.as_view(), name='signup'),
    path('list/', views.JobListView.as_view()),  # alias

        # 🔑 Login & Logout
    path('login/', auth_views.LoginView.as_view(template_name='jobs/auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='jobs:home'), name='logout'),
]
