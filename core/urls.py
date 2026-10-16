from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("careers/", views.career_view, name="careers"),
    path("roadmap/", views.roadmap_view, name="roadmap"),
    path("roadmap/<int:task_id>/toggle/", views.toggle_task, name="toggle_task"),
    path("resume/", views.resume_view, name="resume"),
    path("interview/", views.interview_view, name="interview"),
    path("chatbot/", views.chatbot_view, name="chatbot"),
    path("job-match/", views.job_match_view, name="job_match"),
    path("progress/", views.progress_view, name="progress"),
]
