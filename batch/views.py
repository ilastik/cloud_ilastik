from django.views import generic
from rest_framework import viewsets, response, permissions

from . import serializers, models
from cloud_ilastik.datasets import models as datasets_models


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
