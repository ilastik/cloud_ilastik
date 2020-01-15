from django.views import generic

from cloud_ilastik.datasets.models import Dataset


class ListView(generic.ListView):
    model = Dataset


class DetailView(generic.DetailView):
    model = Dataset
