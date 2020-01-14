from rest_framework import serializers

from . import models


__all__ = ["ProjectSerializer"]


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Project
        fields = ["id", "file", "num_dimensions"]


class BatchJob(serializers.Serializer):
    project = serializers.CharField()
    datasets = serializers.ListField(child=serializers.CharField())


class JobUpdate(serializers.Serializer):
    status = serializers.ChoiceField(choices=[models.JobStatus.done.value, models.JobStatus.failed.value])
