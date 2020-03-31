import pytest
import uuid

from django.urls import reverse
from rest_framework import test, status

from batch.test import factories


pytestmark = pytest.mark.django_db


class TestUpdateStatus:
    @pytest.fixture
    def valid_payload(self):
        return {
            "dtype": "uint8",
            "name": "Result",
            "result_url": "https://example.com/test/",
            "size_x": 64,
            "size_y": 64,
            "status": "done",
        }

    def test_reverse_url(self):
        url = reverse("job-done", kwargs={"external_id": "test-id"})
        assert url == "/v1/batch/jobs/external/test-id/"

    def test_posting_empty_payload(self, api_client: test.APIClient):
        url = reverse("job-done", kwargs={"external_id": "test-id"})
        resp = api_client.put(url, {}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_posting_lists_required_fields(self, api_client: test.APIClient):
        url = reverse("job-done", kwargs={"external_id": "test-id"})
        resp = api_client.put(url, {}, format="json")
        data = resp.json()

        assert isinstance(data, dict)
        assert data.keys() == {"dtype", "name", "result_url", "size_x", "size_y", "status"}

    def test_posting_to_non_existing_id_returns_not_found(self, api_client: test.APIClient, valid_payload):
        url = reverse("job-done", kwargs={"external_id": uuid.uuid4().hex})
        resp = api_client.put(url, valid_payload, format="json")

        assert status.HTTP_404_NOT_FOUND == resp.status_code

    def test_posting_with_valid_result_should_return_successful_status(self, api_client: test.APIClient, valid_payload):
        job = factories.JobFactory(external_id=uuid.uuid4().hex)
        url = reverse("job-done", kwargs={"external_id": job.external_id})
        resp = api_client.put(url, valid_payload, format="json")

        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_posting_with_valid_result_saves_dataset_in_database(self, api_client: test.APIClient, valid_payload):
        job = factories.JobFactory(external_id=uuid.uuid4().hex)
        assert not job.results.exists()

        url = reverse("job-done", kwargs={"external_id": job.external_id})
        api_client.put(url, valid_payload, format="json")

        assert job.results.exists() == 1
        dataset = job.results.first()
        assert dataset.dtype == valid_payload["dtype"]
        assert dataset.size_x == valid_payload["size_x"]
        assert dataset.size_y == valid_payload["size_y"]
        assert dataset.url == valid_payload["result_url"]

class TestProjectList:
    def test_reverse_url(self):
        url = reverse("project-list")
        assert url == "/v1/batch/projects/"

    def test_unauthorized(self, api_client):
        url = reverse("project-list")
        resp = api_client.get(url, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_authorized(self, user, api_client):
        url = reverse("project-list")
        api_client.force_login(user)
        resp = api_client.get(url, format="json")
        assert resp.status_code == status.HTTP_200_OK

    def test_project_list(self, user, api_client):
        url = reverse("project-list")
        projects = factories.ProjectFactory.create_batch(5, file__owner=user)
        api_client.force_login(user)
        resp = api_client.get(url)
        data = resp.json()
        assert len(data) == 5
