import uuid

from django.db import models
from django.contrib.auth import get_user_model

__all__ = ["File"]

User = get_user_model()


class File(models.Model):
    """
    User uploaded file
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    data = models.FileField()
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
