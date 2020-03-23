import pytest

from django.conf import settings
from rest_framework import test

from cloud_ilastik.users.test.factories import UserFactory


@pytest.fixture
def api_rf() -> test.APIRequestFactory:
    return test.APIRequestFactory()


@pytest.fixture
def api_client() -> test.APIClient:
    return test.APIClient()


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user() -> settings.AUTH_USER_MODEL:
    return UserFactory()
