from batch import models
from cloud_ilastik.datasets.tests import factories as datasets_factories
from files.tests import factories as files_factories
import factory


class ProjectFactory(factory.DjangoModelFactory):
    file = factory.SubFactory(files_factories.FileFactory)
    num_channels = 3
    min_block_size_z = 1
    min_block_size_x = 1
    min_block_size_y = 1

    class Meta:
        model = models.Project


class JobFactory(factory.DjangoModelFactory):
    status = models.JobStatus.created.value

    project = factory.SubFactory(ProjectFactory)
    raw_data = factory.SubFactory(datasets_factories.DatasetFactory)

    class Meta:
        model = models.Job
