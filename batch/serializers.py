from rest_framework import serializers

from . import models
import cloud_ilastik.datasets.models as datasets_models


__all__ = ["ProjectSerializer"]


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    html_url = serializers.HyperlinkedIdentityField("batch:project-detail")

    class Meta:
        model = models.Project
        fields = ["id", "html_url", "file", "num_channels", "min_block_size_z", "min_block_size_y", "min_block_size_x"]


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
