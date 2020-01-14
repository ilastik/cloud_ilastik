from django.contrib import admin

from . import models


@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    search_fields = ["file__name"]


@admin.register(models.Job)
class JobAdmin(admin.ModelAdmin):
    pass
