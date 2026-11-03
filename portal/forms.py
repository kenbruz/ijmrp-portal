from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CandidateProfile, CandidateSkill, JobPosting, Skill, User


class RegistrationForm(UserCreationForm):
    account_type = forms.ChoiceField(
        choices=[
            (User.AccountType.JOB_SEEKER, "Job Seeker"),
            (User.AccountType.EMPLOYER, "Employer"),
        ],
        label="I am registering as a",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "account_type")


class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = ("title", "description", "location", "employment_type")
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.skills = list(Skill.objects.order_by("category", "name"))
        for skill in self.skills:
            self.fields[f"weight_{skill.id}"] = forms.DecimalField(
                required=False,
                min_value=0,
                max_value=1,
                max_digits=3,
                decimal_places=2,
                label=skill.name,
                widget=forms.NumberInput(
                    attrs={"step": "0.01", "min": "0", "max": "1", "placeholder": "0 to 1"}
                ),
            )

    def skill_fields(self):
        return [(skill, self[f"weight_{skill.id}"]) for skill in self.skills]

    def clean(self):
        cleaned = super().clean()
        weights = {}
        for skill in self.skills:
            value = cleaned.get(f"weight_{skill.id}")
            if value:
                weights[skill] = value
        if not weights:
            raise forms.ValidationError("Give at least one skill a weight above 0.")
        self.skill_weights = weights
        return cleaned


class CandidateProfileForm(forms.ModelForm):
    EVIDENCE_CHOICES = [
        (CandidateSkill.Evidence.CV_MENTION, "Mentioned in my CV"),
        (CandidateSkill.Evidence.CERTIFICATE, "Certificate"),
        (CandidateSkill.Evidence.PORTFOLIO, "Portfolio / project link"),
    ]

    class Meta:
        model = CandidateProfile
        fields = ("headline", "cv_file", "portfolio_url")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.skills = list(Skill.objects.order_by("category", "name"))
        valid_evidence = [value for value, _ in self.EVIDENCE_CHOICES]
        existing = {}
        if self.instance.pk:
            existing = {cs.skill_id: cs for cs in self.instance.skills.all()}
        for skill in self.skills:
            current = existing.get(skill.id)
            evidence = CandidateSkill.Evidence.CV_MENTION
            if current and current.evidence_type in valid_evidence:
                evidence = current.evidence_type
            self.fields[f"has_{skill.id}"] = forms.BooleanField(
                required=False,
                initial=current is not None,
                widget=forms.CheckboxInput(attrs={"style": "width:auto;margin:0"}),
            )
            self.fields[f"evidence_{skill.id}"] = forms.ChoiceField(
                required=False,
                choices=self.EVIDENCE_CHOICES,
                initial=evidence,
            )

    def skill_fields(self):
        return [
            (skill, self[f"has_{skill.id}"], self[f"evidence_{skill.id}"])
            for skill in self.skills
        ]

    def selected_skills(self):
        chosen = []
        for skill in self.skills:
            if self.cleaned_data.get(f"has_{skill.id}"):
                evidence = (
                    self.cleaned_data.get(f"evidence_{skill.id}")
                    or CandidateSkill.Evidence.CV_MENTION
                )
                chosen.append((skill, evidence))
        return chosen