from rest_framework import serializers

from . import models


__all__ = ["ProjectSerializer"]


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Project
        fields = ["id", "file", "num_dimensions"]
