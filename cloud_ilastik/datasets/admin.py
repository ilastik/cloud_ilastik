from django.contrib import admin

from .models import Dataset


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ["name", "url", "owner", "is_public", "dtype", "size_t", "size_z", "size_y", "size_x", "size_c"]
    search_fields = ["name", "url"]
