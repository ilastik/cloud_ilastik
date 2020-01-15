from pathlib import Path

from django.views import generic
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, response, permissions, generics

from . import serializers, models
from cloud_ilastik.datasets import models as datasets_models

import hpc


_30_MINUTES = 30 * 60


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
        serializer = serializers.BatchJob(data=request.data)
        serializer.is_valid(raise_exception=True)
        proj = models.Project.objects.only("file__data").get(id=serializer.data["project"])
        datasets = datasets_models.Dataset.objects.filter(id__in=serializer.data["datasets"])
        jobs = []

        for ds in datasets:
            jobs.append(models.Job(project=proj, raw_data=ds, owner=request.user))

        models.Job.objects.bulk_create(jobs)

        # submit jobs
        for job in jobs:
            proj_file_path = job.project.file.data.path
            jobspec = hpc.IlastikJobSpec(
                ilp_project=Path(proj_file_path),
                raw_data_url=job.raw_data.tar_url,
                result_endpoint="http://web.ilastik.org/v1/batch/jobs/external",
                Resources=hpc.JobResources(CPUs=10, Memory="32G", Runtime=_30_MINUTES),
            )
            unicore_job = jobspec.run()
            job.external_id = unicore_job.job_id
            job.status = models.JobStatus.running.value
            job.save()

        return response.Response(status=204)


class JobDoneView(generics.UpdateAPIView):
    def update(self, request, external_id: str):
        serializer = serializers.JobUpdate(data=request.data, context={"request": request})
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
                **{k: v for k, v in serializer.data.items() if k.startswith("size_")},
                "job": job,
            }
            datasets_models.Dataset(**dataset_params).save()

        return response.Response(status=204)
