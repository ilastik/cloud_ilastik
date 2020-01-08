from rest_framework import serializers

from . import models


__all__ = ["FileSerializer"]


class FileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.File
        fields = ["id", "url", "name", "data"]
