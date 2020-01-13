import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from files import models as file_models


__all__ = ["Project"]


def not_negative(value):
    if value < 0:
        raise ValidationError(_('%(value)s should be positive or 0'), params={'value': value})


class Project(models.Model):
    """
    User project
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(file_models.File, on_delete=models.SET_NULL, null=True)
    num_channels = models.PositiveIntegerField()
    min_block_size_z = models.IntegerField(default=0, validators=[not_negative])
    min_block_size_y = models.IntegerField(validators=[not_negative])
    min_block_size_x = models.IntegerField(validators=[not_negative])

    @property
    def name(self):
        return self.file.name if self.file else self.id

    @property
    def min_block_sizes(self):
        return {'z': self.min_block_size_z, 'y': self.min_block_size_y, 'x': self.min_block_size_x}

    def __str__(self):
        name = self.file.name if self.file else f'<<<{self.id}>>>'
        channels = '1 channel' if self.num_channels == 1 else f'{self.num_channels} channels'
        return f'{name} [{channels}]'
