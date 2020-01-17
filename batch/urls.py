from django.urls import path

from . import views

app_name = "batch"
urlpatterns = [
    path("projects/", views.ProjectListView.as_view(), name="project-list"),
    path("projects/<uuid:pk>/jobs", views.ProjectDetailView.as_view(), name="project-detail"),
    path("projects/<uuid:pk>/jobs/new/", views.ProjectNewJobView.as_view(), name="project-new-job"),
]
