import uuid

from django.db import models

from files import models as file_models


__all__ = ["Project"]


class Project(models.Model):
    """
    User project
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(file_models.File, on_delete=models.SET_NULL, null=True)
    num_dimensions = models.PositiveIntegerField()
