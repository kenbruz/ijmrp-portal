from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    CandidateProfile,
    CandidateSkill,
    JobPosting,
    JobSkillRequirement,
    MatchScore,
    Skill,
    User,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Account type", {"fields": ("account_type",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Account type", {"fields": ("email", "account_type")}),
    )
    list_display = ("username", "email", "account_type", "is_staff")
    list_filter = UserAdmin.list_filter + ("account_type",)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "category")
    search_fields = ("name", "aliases")


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ("title", "employer", "employment_type", "date_posted")


admin.site.register(CandidateProfile)
admin.site.register(CandidateSkill)
admin.site.register(JobSkillRequirement)
admin.site.register(MatchScore)