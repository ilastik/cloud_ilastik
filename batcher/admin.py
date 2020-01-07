from django.contrib import admin

from . import models


@admin.register(models.File)
class FileAdmin(admin.ModelAdmin):
    search_fields = ["name"]
