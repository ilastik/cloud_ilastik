from django.contrib import admin

from . import models


@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    search_fields = ["file__name"]


@admin.register(models.Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ["id", "owner", "status", "project", "external_id", "created_on", "updated_on"]
    readonly_fields = ["owner", "project", "external_id", "created_on", "updated_on"]
    list_filter = ["status", "created_on"]
    search_fields = ["id", "owner__username"]
    ordering = ["-created_on"]
