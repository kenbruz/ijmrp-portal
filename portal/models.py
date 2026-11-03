from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class User(AbstractUser):
    """Every account on the portal: job seeker, employer or admin."""

    class AccountType(models.TextChoices):
        JOB_SEEKER = "job_seeker", "Job Seeker"
        EMPLOYER = "employer", "Employer"
        ADMIN = "admin", "Admin"

    email = models.EmailField(unique=True)
    account_type = models.CharField(
        max_length=20,
        choices=AccountType.choices,
        default=AccountType.JOB_SEEKER,
    )

    def __str__(self):
        return f"{self.username} ({self.get_account_type_display()})"


class Skill(models.Model):
    """One skill in the platform's skill library."""

    name = models.CharField(max_length=100, unique=True)
    definition = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    aliases = models.TextField(
        blank=True,
        help_text="Alternative names or abbreviations, separated by commas",
    )

    def __str__(self):
        return self.name


class CandidateProfile(models.Model):
    """Extra details for a job seeker, linked one-to-one with a User."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidate_profile",
    )
    headline = models.CharField(max_length=200, blank=True)
    cv_file = models.FileField(upload_to="cvs/", blank=True)
    portfolio_url = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


class CandidateSkill(models.Model):
    """A skill a candidate has, plus the evidence behind the claim."""

    class Evidence(models.TextChoices):
        CV_MENTION = "cv_mention", "Detected in CV"
        CERTIFICATE = "certificate", "Verified certificate"
        ASSESSMENT = "assessment", "In-platform assessment"
        PORTFOLIO = "portfolio", "Portfolio link"

    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="skills",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="candidate_skills",
    )
    evidence_type = models.CharField(
        max_length=20,
        choices=Evidence.choices,
        default=Evidence.CV_MENTION,
    )
    confidence = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Strength of the evidence, from 0 to 1",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "skill"], name="unique_candidate_skill"
            )
        ]

    def __str__(self):
        return f"{self.candidate.user.username} - {self.skill.name}"


class JobPosting(models.Model):
    """A job advert posted by an employer."""

    class EmploymentType(models.TextChoices):
        FULL_TIME = "full_time", "Full-time"
        PART_TIME = "part_time", "Part-time"
        CONTRACT = "contract", "Contract"
        REMOTE = "remote", "Remote"

    employer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_postings",
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200, blank=True)
    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
    )
    date_posted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class JobSkillRequirement(models.Model):
    """A skill a job requires, and how much the employer values it."""

    job = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name="skill_requirements",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="job_requirements",
    )
    weight = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Importance of this skill for the job, from 0 to 1",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["job", "skill"], name="unique_job_skill"
            )
        ]

    def __str__(self):
        return f"{self.job.title} - {self.skill.name} ({self.weight})"


class MatchScore(models.Model):
    """The result of matching one candidate against one job."""

    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="match_scores",
    )
    job = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name="match_scores",
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Overall match score, from 0 to 100",
    )
    breakdown = models.JSONField(
        default=dict,
        blank=True,
        help_text="How much each skill contributed to the score",
    )
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "job"], name="unique_candidate_job_match"
            )
        ]

    def __str__(self):
        return f"{self.candidate.user.username} -> {self.job.title}: {self.score}"