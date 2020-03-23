from files import models

import factory


class FileFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: "file_%d" % n)
    data = factory.django.FileField(filename="the_file.dat")

    class Meta:
        model = models.File
