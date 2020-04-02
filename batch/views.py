from django import urls
from django.contrib.auth import mixins
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.views import generic
from django.shortcuts import get_object_or_404, render
from rest_framework import viewsets, response, permissions, generics

from . import serializers, models
from cloud_ilastik.datasets import models as datasets_models


@login_required()
def project_list_page(request):
    return render(request, "batch/project_list.html")


class ProjectDetailView(mixins.LoginRequiredMixin, mixins.UserPassesTestMixin, generic.DetailView):
    model = models.Project

    def test_func(self):
        project = self.get_object()
        return project.is_public or project.file and project.file.owner_id == self.request.user.id

    def get_context_data(self, **kwargs):
        return super().get_context_data(nav_list=self._nav_list, **kwargs)

    @property
    def _nav_list(self):
        data = [
            {"view_name": "batch:project-detail", "title": "Jobs"},
            {"view_name": "batch:project-new-job", "title": "New Job"},
        ]

        result = []
        for d in data:
            url = urls.reverse(d["view_name"], args=[self.object.pk])
            classes = ["nav-link"]
            if url == self.request.path:
                classes.append("active")
            result.append({"url": url, "class": " ".join(classes), "title": d["title"]})

        return result


class ProjectNewJobView(ProjectDetailView):
    template_name_suffix = "_new_job"

    def get_context_data(self, **kwargs):
        return super().get_context_data(dataset_list=self._compatible_datasets, **kwargs)

    def post(self, request, *args, **kwargs):
        project = self.get_object()

        try:
            prefix = "dataset-"
            # Is it an error if there are no datasets, or some datasets in the request are not in the compatible set?
            datasets = self._compatible_datasets.filter(
                id__in=(int(k[len(prefix) :]) for k in self.request.POST if k.startswith(prefix))
            )
        except (KeyError, ValueError):
            return HttpResponse(status=400)

        models.Job.objects.bulk_create(
            models.Job(project=project, owner=self.request.user, raw_data=dataset) for dataset in datasets
        )
        return HttpResponseRedirect(urls.reverse("batch:project-detail", args=[project.pk]))

    @property
    def _compatible_datasets(self):
        project = self.get_object()
        return datasets_models.Dataset.objects.filter(
            Q(is_public=True) | Q(owner=self.request.user),
            size_z__gte=project.min_block_size_z,
            size_y__gte=project.min_block_size_y,
            size_x__gte=project.min_block_size_x,
            size_c=project.num_channels,
        )


class ProjectViewset(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        serializer = serializers.ProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = models.Project.objects.create(**serializer.validated_data)

        serializer = serializers.ProjectSerializer(project, context={"request": request})
        return response.Response(serializer.data)

    def list(self, request):
        queryset = models.Project.objects.filter(Q(file__owner=request.user) | Q(is_public=True))
        serializer = serializers.ProjectSerializer(queryset, many=True, context={"request": request})
        return response.Response(serializer.data)


class JobViewset(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.JobSerializer

    def get_queryset(self):
        return (
            models.Job.objects.select_related("raw_data", "project")
            .prefetch_related("results")
            .filter(project_id=self.kwargs["project_id"])
            .order_by("-created_on")
        )


class BatchJobViewset(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        serializer = serializers.BatchJob(data=request.data)
        serializer.is_valid(raise_exception=True)
        proj = models.Project.objects.only("file__data").get(id=serializer.data["project"])
        datasets = datasets_models.Dataset.objects.filter(id__in=serializer.data["datasets"])
        jobs = []

        for ds in datasets:
            jobs.append(models.Job(project=proj, raw_data=ds, owner=request.user))

        models.Job.objects.bulk_create(jobs)

        # submit jobs
        return response.Response(status=204)


class JobDoneView(generics.UpdateAPIView):
    def update(self, request, external_id: str):
        serializer = serializers.JobUpdate(data=request.data)
        serializer.is_valid(raise_exception=True)

        status = serializer.data["status"]

        job = get_object_or_404(models.Job, external_id=external_id)
        job.status = status
        job.save()

        if status == "done":
            dataset_params = {
                "name": serializer.data["name"],
                "url": serializer.data["result_url"],
                "dtype": serializer.data["dtype"],
                "channel_type": serializer.data["channel_type"],
                **{k: v for k, v in serializer.data.items() if k.startswith("size_")},
                "job": job,
            }
            datasets_models.Dataset(**dataset_params).save()

        return response.Response(status=204)
