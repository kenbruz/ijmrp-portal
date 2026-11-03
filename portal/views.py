from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import CandidateProfileForm, JobPostingForm, RegistrationForm
from .models import (
    CandidateProfile,
    CandidateSkill,
    JobPosting,
    JobSkillRequirement,
    User,
)

# Strength of the evidence behind a skill claim, from 0 to 1.
EVIDENCE_CONFIDENCE = {
    CandidateSkill.Evidence.CV_MENTION: 0.4,
    CandidateSkill.Evidence.CERTIFICATE: 0.6,
    CandidateSkill.Evidence.ASSESSMENT: 0.8,
    CandidateSkill.Evidence.PORTFOLIO: 1.0,
}


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user.account_type == User.AccountType.JOB_SEEKER:
                CandidateProfile.objects.create(user=user)
            login(request, user)
            return redirect("dashboard")
    else:
        form = RegistrationForm()
    return render(request, "portal/register.html", {"form": form})


@login_required
def dashboard(request):
    return render(request, "portal/dashboard.html")


@login_required
def post_job(request):
    if request.user.account_type != User.AccountType.EMPLOYER:
        return redirect("dashboard")
    if request.method == "POST":
        form = JobPostingForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                job = form.save(commit=False)
                job.employer = request.user
                job.save()
                for skill, weight in form.skill_weights.items():
                    JobSkillRequirement.objects.create(
                        job=job, skill=skill, weight=weight
                    )
            return redirect("my_jobs")
    else:
        form = JobPostingForm()
    return render(request, "portal/post_job.html", {"form": form})


@login_required
def my_jobs(request):
    if request.user.account_type != User.AccountType.EMPLOYER:
        return redirect("dashboard")
    jobs = (
        JobPosting.objects.filter(employer=request.user)
        .prefetch_related("skill_requirements__skill")
        .order_by("-date_posted")
    )
    return render(request, "portal/my_jobs.html", {"jobs": jobs})


@login_required
def edit_profile(request):
    if request.user.account_type != User.AccountType.JOB_SEEKER:
        return redirect("dashboard")
    profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = CandidateProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            with transaction.atomic():
                profile = form.save()
                chosen = form.selected_skills()
                profile.skills.exclude(skill__in=[skill for skill, _ in chosen]).delete()
                for skill, evidence in chosen:
                    CandidateSkill.objects.update_or_create(
                        candidate=profile,
                        skill=skill,
                        defaults={
                            "evidence_type": evidence,
                            "confidence": EVIDENCE_CONFIDENCE[evidence],
                        },
                    )
            return redirect(f"{reverse('edit_profile')}?saved=1")
    else:
        form = CandidateProfileForm(instance=profile)
    return render(request, "portal/edit_profile.html", {"form": form})