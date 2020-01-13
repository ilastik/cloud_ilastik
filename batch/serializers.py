from rest_framework import serializers

from . import models


__all__ = ["ProjectSerializer"]


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    html_url = serializers.HyperlinkedIdentityField("batch:project-detail")

    class Meta:
        model = models.Project
        fields = ["id", "html_url", "file", "num_channels", "min_block_size_z", "min_block_size_y", "min_block_size_x"]
