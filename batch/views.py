from pathlib import Path

from django.views import generic
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, response, permissions, generics

from . import serializers, models
from cloud_ilastik.datasets import models as datasets_models

import hpc


class ProjectListView(generic.ListView):
    def get_queryset(self):
        return models.Project.objects.filter(file__owner_id=self.request.user.id)


class ProjectDetailView(generic.DetailView):
    model = models.Project

    @property
    def _compatible_datasets(self):
        return datasets_models.Dataset.objects.filter(
            size_z__gte=self.object.min_block_size_z,
            size_y__gte=self.object.min_block_size_y,
            size_x__gte=self.object.min_block_size_x,
            size_c=self.object.num_channels,
        )

    def get_context_data(self, **kwargs):
        return super().get_context_data(dataset_list=self._compatible_datasets, **kwargs)


class ProjectViewset(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        serializer = serializers.ProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = models.Project.objects.create(**serializer.validated_data)

        serializer = serializers.ProjectSerializer(project, context={"request": request})
        return response.Response(serializer.data)

    def list(self, request):
        queryset = models.Project.objects.filter(file__owner=request.user)
        serializer = serializers.ProjectSerializer(queryset, many=True)
        return response.Response(serializer.data)


class BatchJobViewset(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):

        jobspec = hpc.IlastikJobSpec(
            ilp_project=Path("hbp_proj.ilp"),
            raw_data_url="some",
            result_endpoint="http://web.ilastik.org/v1/batch/jobs/external",
            Resources=hpc.JobResources(CPUs=3, Memory="32G"),
        )
        job = jobspec.run()
        serializer = serializers.BatchJob(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        models.Job.objects.create(owner=user, external_id=job.job_id)
        return response.Response(serializer.data)


class JobDoneView(generics.UpdateAPIView):
    def update(self, request, external_id: str):
        serializer = serializers.JobUpdate(data=request.data)
        serializer.is_valid(raise_exception=True)

        job = get_object_or_404(models.Job, external_id=external_id)
        job.status = serializer.data["status"]
        job.save()

        return response.Response(status=204)
