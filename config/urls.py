"""URL configuration for the IJMRP project."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import RedirectView

from portal import match_views, views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(pattern_name='login', permanent=False)),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='portal/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('jobs/', views.my_jobs, name='my_jobs'),
    path('jobs/new/', views.post_job, name='post_job'),
    path('jobs/<int:job_id>/matches/', match_views.employer_matches, name='employer_matches'),
    path('my-matches/', match_views.job_matches, name='job_matches'),
    path('profile/', views.edit_profile, name='edit_profile'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
