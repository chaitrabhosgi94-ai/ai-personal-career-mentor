from io import BytesIO
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from pypdf import PdfReader
from .forms import RegisterForm, ProfileForm
from .models import UserProfile, RoadmapTask, InterviewAttempt
from .services import recommend_careers, compare_job
from .ai import ask_ai

def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "core/home.html")

def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        UserProfile.objects.create(user=user)
        login(request, user)
        messages.success(request, "Account created. Complete your career profile to get started.")
        return redirect("profile")
    return render(request, "core/register.html", {"form": form})

def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("dashboard")
    return render(request, "core/login.html", {"form": form})

@require_POST
def logout_view(request):
    logout(request)
    return redirect("home")

@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been saved.")
        return redirect("dashboard")
    return render(request, "core/profile.html", {"form": form})

@login_required
def dashboard(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    tasks = RoadmapTask.objects.filter(user=request.user)
    total = tasks.count()
    completed = tasks.filter(completed=True).count()
    progress = round(completed * 100 / total) if total else 0
    recs = recommend_careers(profile.skills, profile.interests)[:3]
    return render(request, "core/dashboard.html", {
        "profile": profile, "tasks": tasks[:5], "total": total,
        "completed": completed, "progress": progress, "recommendations": recs,
        "interviews": InterviewAttempt.objects.filter(user=request.user)[:3],
    })

@login_required
def career_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    skills = request.POST.get("skills", profile.skills)
    interests = request.POST.get("interests", profile.interests)
    results = recommend_careers(skills, interests)
    return render(request, "core/careers.html", {
        "results": results, "skills": skills, "interests": interests
    })

@login_required
def roadmap_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    role = request.POST.get("role", profile.target_role or "Python Developer")
    tasks = RoadmapTask.objects.filter(user=request.user)
    if request.method == "POST" and request.POST.get("generate"):
        RoadmapTask.objects.filter(user=request.user).delete()
        default_steps = [
            ("Core foundations", f"Review the fundamentals required for {role}."),
            ("Build a small project", f"Create a beginner project that demonstrates {role} skills."),
            ("Practice problem solving", "Complete practice exercises and explain your approach."),
            ("Create a portfolio project", "Build and document a project with Git and a clear README."),
            ("Resume and interview preparation", f"Tailor your resume and practice questions for {role}."),
        ]
        ai_text = ask_ai(
            "You are a practical career mentor. Return 5 concise learning roadmap tasks, one per line.",
            f"Create a beginner-to-job-ready roadmap for {role}. Current skills: {profile.skills}. Interests: {profile.interests}.",
            "\n".join(f"{title}: {desc}" for title, desc in default_steps)
        )
        lines = [line.strip(" -•\t") for line in ai_text.splitlines() if line.strip() and not line.strip().startswith("[Demo mode:") and not line.strip().startswith("[AI service is currently unavailable")]
        if len(lines) < 3:
            lines = [f"{title}: {desc}" for title, desc in default_steps]
        for line in lines[:8]:
            title, sep, desc = line.partition(":")
            RoadmapTask.objects.create(user=request.user, title=(title[:180] if sep else line[:180]), description=(desc.strip() if sep else "Work through this learning step."), category="Learning")
        messages.success(request, "Your roadmap has been generated.")
        return redirect("roadmap")
    tasks = RoadmapTask.objects.filter(user=request.user)
    return render(request, "core/roadmap.html", {"tasks": tasks, "role": role})

@login_required
@require_POST
def toggle_task(request, task_id):
    task = get_object_or_404(RoadmapTask, id=task_id, user=request.user)
    task.completed = not task.completed
    task.save(update_fields=["completed"])
    return redirect("roadmap")

@login_required
def resume_view(request):
    result = None
    error = None
    if request.method == "POST":
        upload = request.FILES.get("resume")
        if not upload:
            error = "Please choose a PDF resume."
        elif not upload.name.lower().endswith(".pdf"):
            error = "Only PDF files are supported."
        elif upload.size > 5 * 1024 * 1024:
            error = "Please upload a PDF smaller than 5 MB."
        else:
            try:
                reader = PdfReader(BytesIO(upload.read()))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)[:18000]
                if not text.strip():
                    error = "No selectable text found. Try exporting your resume as a text-based PDF."
                else:
                    result = ask_ai(
                        "You are a constructive resume coach. Review only the resume text supplied. Do not invent qualifications. Give: strengths, missing details, measurable-impact suggestions, ATS keywords, and 3 next actions. Be respectful.",
                        f"Target role: {request.POST.get('target_role', 'Entry-level software developer')}\nResume text:\n{text}",
                        "Resume review checklist:\n- Put contact details, education, skills, and projects in clearly labeled sections.\n- Start project bullets with action verbs and explain the result or impact.\n- Tailor skills to the target role and include relevant keywords from the job description.\n- Keep formatting consistent and proofread carefully.\n- Add links to GitHub or a portfolio when available."
                    )
            except Exception:
                error = "Could not read this PDF. Please try another text-based PDF."
    return render(request, "core/resume.html", {"result": result, "error": error})

@login_required
def interview_view(request):
    question = None
    feedback = None
    role = request.POST.get("role", "Python Developer")
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "question":
            question = ask_ai(
                "You are a technical interviewer. Return exactly one clear interview question and no answer.",
                f"Ask one {request.POST.get('level', 'junior')} level interview question for the role: {role}. Topic preference: {request.POST.get('topic', 'mixed technical')}.",
                f"Explain the difference between a list and a tuple in Python, and give one practical use case for each."
            )
        elif action == "evaluate":
            q = request.POST.get("question", "")
            answer = request.POST.get("answer", "").strip()
            if q and answer:
                feedback = ask_ai(
                    "You are a fair interview coach. Give constructive feedback, mention what is correct, what is missing, and a stronger sample answer. Do not claim an objective score unless you explain it is approximate.",
                    f"Role: {role}\nQuestion: {q}\nCandidate answer: {answer}",
                    "Feedback:\n- Make your answer more structured: define the concept, explain how it works, and give an example.\n- Include relevant technical terms and mention a practical use case.\n- Practice keeping the answer concise and specific."
                )
                InterviewAttempt.objects.create(user=request.user, role=role, question=q, answer=answer, feedback=feedback)
                question = q
    return render(request, "core/interview.html", {"question": question, "feedback": feedback, "role": role})

@login_required
def chatbot_view(request):
    answer = None
    prompt = ""
    if request.method == "POST":
        prompt = request.POST.get("message", "").strip()[:4000]
        if prompt:
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            answer = ask_ai(
                "You are an encouraging, realistic career mentor for students and early-career job seekers. Give practical steps. Do not guarantee jobs or fabricate current openings.",
                f"User profile: education={profile.education}; skills={profile.skills}; interests={profile.interests}; target role={profile.target_role}.\nQuestion: {prompt}",
                "Start by defining the goal, list the skills you already have, identify one skill gap, and choose a small project to demonstrate progress. If you share your target role and current skills, I can help you create a more specific plan."
            )
    return render(request, "core/chatbot.html", {"answer": answer, "prompt": prompt})

@login_required
def job_match_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    result = None
    description = ""
    if request.method == "POST":
        description = request.POST.get("description", "")[:12000]
        skills = request.POST.get("skills", profile.skills)
        result = compare_job(skills, description)
        if description.strip():
            result["advice"] = ask_ai(
                "You are a job-description and skills matching coach. Be honest and do not claim the user is qualified solely from keyword overlap.",
                f"Known skills: {skills}\nJob description:\n{description}\nKeyword comparison: matched={result['matched']}; missing={result['missing']}. Give 4 actionable recommendations.",
                "Focus on the missing skills that appear most important in the job description. Build one project demonstrating a priority skill, update your resume with truthful evidence, and prepare examples for interviews."
            )
    return render(request, "core/job_match.html", {"result": result, "description": description, "skills": profile.skills})

@login_required
def progress_view(request):
    tasks = RoadmapTask.objects.filter(user=request.user)
    total = tasks.count()
    completed = tasks.filter(completed=True).count()
    progress = round(completed * 100 / total) if total else 0
    attempts = InterviewAttempt.objects.filter(user=request.user)
    return render(request, "core/progress.html", {"tasks": tasks, "total": total, "completed": completed, "progress": progress, "attempts": attempts[:10]})
