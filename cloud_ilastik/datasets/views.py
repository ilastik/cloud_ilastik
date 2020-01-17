from django.contrib.auth import mixins
from django.db.models import Q
from django.views import generic

from cloud_ilastik.datasets.models import Dataset


class ListView(generic.ListView):
    def get_queryset(self):
        query = Q(is_public=True)
        if not self.request.user.is_anonymous:
            query |= Q(owner=self.request.user)
        return Dataset.objects.filter(query).order_by("-created_on")


class DetailView(mixins.UserPassesTestMixin, generic.DetailView):
    model = Dataset

    def test_func(self):
        dataset = self.get_object()
        return dataset.is_public or dataset.owner == self.request.user
