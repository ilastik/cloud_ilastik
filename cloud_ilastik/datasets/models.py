from django.db import models


class Dataset(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField()
    size_t = models.PositiveIntegerField(default=1)
    size_z = models.PositiveIntegerField(default=1)
    size_y = models.PositiveIntegerField()
    size_x = models.PositiveIntegerField()
    size_c = models.PositiveIntegerField(default=1)

    @property
    def sizes(self):
        return {'t': self.size_t, 'z': self.size_z, 'y': self.size_y, 'x': self.size_x, 'c': self.size_c}

    def __str__(self):
        return f'{self.name} {self.sizes} <{self.url}>'
