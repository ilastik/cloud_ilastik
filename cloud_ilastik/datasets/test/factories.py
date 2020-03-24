from cloud_ilastik.datasets import models

import factory


class DatasetFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: "dataset_%d" % n)
    url = factory.Sequence(lambda n: "https://example.com/dataset_%d/" % n)
    dtype = models.DType.float32.value
    size_t = 1
    size_c = 3
    size_z = 1
    size_x = 2000
    size_y = 2000
    is_public = True

    class Meta:
        model = models.Dataset
