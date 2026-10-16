from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ("education", "skills", "interests", "target_role")
        widgets = {
            "education": forms.TextInput(attrs={"placeholder": "e.g. B.E. Computer Science"}),
            "skills": forms.Textarea(attrs={"rows": 3, "placeholder": "Python, Django, SQL, HTML, CSS"}),
            "interests": forms.Textarea(attrs={"rows": 2, "placeholder": "AI, web development, data"}),
            "target_role": forms.TextInput(attrs={"placeholder": "e.g. Python Developer"}),
        }
