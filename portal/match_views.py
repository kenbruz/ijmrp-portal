"""
Matching pages for the portal.

Employer: sees every registered job seeker ranked for one of their jobs.
Job seeker: sees every posted job ranked for them, with skill gaps.
Every result is saved in the MatchScore table.

There is no job-application table in this version, so matching runs across
all registered candidates and all posted jobs.
"""
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .matching import compute_match
from .models import CandidateProfile, JobPosting, MatchScore, User


def _candidate_skills(profile):
    """{skill name: confidence} for one candidate."""
    return {cs.skill.name: cs.confidence for cs in profile.skills.all()}


def _job_skills(job):
    """{skill name: weight} for one job."""
    return {req.skill.name: float(req.weight) for req in job.skill_requirements.all()}


def _match_and_save(profile, job, candidate_skills, job_skills):
    """Work out the score and store it in the MatchScore table."""
    result = compute_match(candidate_skills, job_skills)
    MatchScore.objects.update_or_create(
        candidate=profile,
        job=job,
        defaults={
            "score": Decimal(str(result["score"])),
            "breakdown": {"points": result["breakdown"], "gaps": result["gaps"]},
        },
    )
    return result


@login_required
def employer_matches(request, job_id):
    """Candidates ranked for one job. Only the employer who posted it can open this."""
    if request.user.account_type != User.AccountType.EMPLOYER:
        return redirect("dashboard")

    job = get_object_or_404(
        JobPosting.objects.prefetch_related("skill_requirements__skill"),
        pk=job_id,
        employer=request.user,
    )
    job_skills = _job_skills(job)

    profiles = CandidateProfile.objects.select_related("user").prefetch_related(
        "skills__skill"
    )
    rows = []
    for profile in profiles:
        result = _match_and_save(profile, job, _candidate_skills(profile), job_skills)
        rows.append(
            {
                "profile": profile,
                "score": result["score"],
                "points": result["breakdown"],
                "gaps": result["gaps"],
            }
        )
    rows.sort(key=lambda row: row["score"], reverse=True)
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank

    return render(request, "portal/employer_matches.html", {"job": job, "rows": rows})


@login_required
def job_matches(request):
    """Jobs ranked for the signed-in job seeker, with the skills they are missing."""
    if request.user.account_type != User.AccountType.JOB_SEEKER:
        return redirect("dashboard")

    profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
    candidate_skills = _candidate_skills(profile)

    jobs = JobPosting.objects.select_related("employer").prefetch_related(
        "skill_requirements__skill"
    )
    rows = []
    for job in jobs:
        result = _match_and_save(profile, job, candidate_skills, _job_skills(job))
        rows.append(
            {
                "job": job,
                "score": result["score"],
                "points": result["breakdown"],
                "gaps": result["gaps"],
            }
        )
    rows.sort(key=lambda row: row["score"], reverse=True)
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank

    return render(
        request,
        "portal/job_matches.html",
        {"rows": rows, "has_skills": bool(candidate_skills)},
    )
