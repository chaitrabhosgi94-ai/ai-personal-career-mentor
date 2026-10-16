from django.contrib import admin
from .models import UserProfile, RoadmapTask, InterviewAttempt

admin.site.register(UserProfile)
admin.site.register(RoadmapTask)
admin.site.register(InterviewAttempt)
