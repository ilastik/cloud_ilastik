from django.contrib import admin
from django.urls import reverse
from django.utils.html import escape, mark_safe

from . import models


@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    search_fields = ["file__name"]


@admin.register(models.Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ["id", "owner", "status", "project", "external_id", "created_on", "updated_on"]
    readonly_fields = ["owner", "raw_data_link", "project_link", "external_id", "created_on", "updated_on"]
    list_filter = ["status", "created_on"]
    search_fields = ["id", "owner__username"]
    ordering = ["-created_on"]

    @mark_safe
    def raw_data_link(self, obj: models.Job):
        raw_data = obj.raw_data
        if not raw_data:
            return ""

        link = reverse("admin:datasets_dataset_change", args=[raw_data.id])
        return f'<a href="{link}">{escape(raw_data.name)}</a>'

    raw_data_link.short_description = "Raw Data"

    @mark_safe
    def project_link(self, obj: models.Job):
        project = obj.project
        if not project:
            return ""

        link = reverse("admin:batch_project_change", args=[project.id])
        return f'<a href="{link}">{escape(project.file.name)}</a>'

    project_link.short_description = "Project"
