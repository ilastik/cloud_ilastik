from django.urls import path

from . import views

app_name = "batch"
urlpatterns = [
    path("projects/", views.ProjectListView.as_view(), name="project-list"),
    path("projects/<uuid:pk>/", views.ProjectDetailView.as_view(), name="project-detail"),
]
