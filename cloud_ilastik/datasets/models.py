from django.db import models

import batch.models as batch_models


class Dataset(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField()
    size_t = models.PositiveIntegerField(default=1)
    size_z = models.PositiveIntegerField(default=1)
    size_y = models.PositiveIntegerField()
    size_x = models.PositiveIntegerField()
    size_c = models.PositiveIntegerField(default=1)
    job = models.ForeignKey(batch_models.Job, on_delete=models.SET_NULL, null=True, blank=True, default=None)

    @property
    def owner(self):
        return self.job.owner if self.job else None

    @property
    def sizes(self):
        return {'t': self.size_t, 'z': self.size_z, 'y': self.size_y, 'x': self.size_x, 'c': self.size_c}

    def __str__(self):
        return f'{self.name} {self.sizes} <{self.url}>'
