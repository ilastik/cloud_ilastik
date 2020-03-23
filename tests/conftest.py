import pytest

from rest_framework import test


@pytest.fixture
def api_rf() -> test.APIRequestFactory:
    return test.APIRequestFactory()


@pytest.fixture
def api_client() -> test.APIClient:
    return test.APIClient()
