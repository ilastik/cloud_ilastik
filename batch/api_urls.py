from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("projects", views.ProjectViewset, basename="project")
router.register("batch_jobs", views.BatchJobViewset, basename="batch_job")

urlpatterns = [path("jobs/external/<str:external_id>/", views.JobDoneView.as_view())] + router.urls
