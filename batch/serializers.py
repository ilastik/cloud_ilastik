from typing import Optional

from rest_framework import serializers

from . import models
import cloud_ilastik.datasets.models as datasets_models
from cloud_ilastik.datasets import neuroglancer as ng


__all__ = ["ProjectSerializer"]


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    html_url = serializers.HyperlinkedIdentityField("batch:project-new-job")

    class Meta:
        model = models.Project
        fields = ["id", "html_url", "file", "num_channels", "min_block_size_z", "min_block_size_y", "min_block_size_x"]


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = datasets_models.Dataset
        fields = ["neuroglancer_url"]


class JobSerializer(serializers.HyperlinkedModelSerializer):
    viewer_url = serializers.SerializerMethodField()

    def get_viewer_url(self, obj: models.Job) -> Optional[str]:
        result = obj.results.first()

        if not (result and obj.raw_data):
            return None

        return ng.viewer_url(
            [
                ng.Layer(obj.raw_data.url, obj.raw_data.size_c, role="raw_data"),
                ng.Layer(result.url, result.size_c, role="results", selected=True),
            ],
            show_control_panel=True,
        )

    class Meta:
        model = models.Job
        fields = ["id", "status", "created_on", "viewer_url"]


class BatchJob(serializers.Serializer):
    project = serializers.PrimaryKeyRelatedField(queryset=models.Project.objects.all(), allow_null=False)
    datasets = serializers.PrimaryKeyRelatedField(
        many=True, queryset=datasets_models.Dataset.objects.all(), allow_null=False
    )

    class Meta:
        fields = ["project", "datasets"]


class JobUpdate(serializers.Serializer):
    status = serializers.ChoiceField(choices=[models.JobStatus.done.value, models.JobStatus.failed.value])
    result_url = serializers.URLField()
    name = serializers.CharField()
    dtype = serializers.ChoiceField(choices=datasets_models.DType.values())
    size_t = serializers.IntegerField(default=1)
    size_z = serializers.IntegerField(default=1)
    size_y = serializers.IntegerField()
    size_x = serializers.IntegerField()
    size_c = serializers.IntegerField(default=1)
