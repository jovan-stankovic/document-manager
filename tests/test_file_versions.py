import pytest
from django.core.files.base import ContentFile
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from propylon_document_manager.file_versions.models import FileVersion, User


def test_file_versions():
    file_name = "new_file"
    file_version = 1
    FileVersion.objects.create(file_name=file_name, version_number=file_version)
    files = FileVersion.objects.all()
    assert files.count() == 1
    assert files[0].file_name == file_name
    assert files[0].version_number == file_version


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_user_registration(api_client):
    """Test user registration endpoint."""
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "complexpassword123",
    }
    response = api_client.post(reverse("user_register"), user_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["email"] == user_data["email"]
    assert response.data["name"] == user_data["name"]


@pytest.mark.django_db
def test_user_login(api_client):
    """Test user login endpoint."""
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "complexpassword123",
    }
    api_client.post(reverse("user_register"), user_data)
    user = User.objects.get()
    response = api_client.post(reverse("custom-login"), {"username": user.email, "password": user_data["password"]})
    assert response.status_code == status.HTTP_200_OK
    assert "token" in response.data


@pytest.mark.django_db
def test_file_version_creation(api_client, user):
    """Test file version creation endpoint."""
    api_client.force_authenticate(user=user)
    content = ContentFile(b"Sample file content", name="sample.txt")
    file_data = {"file_name": "sample", "file": content, "url": "test-url"}

    response = api_client.post("/api/file_versions/", file_data, format="multipart")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["file_name"] == file_data["file_name"]
    assert response.data["user"] == user.id


@pytest.mark.django_db
def test_get_file_version_by_url(api_client, file_version):
    """Test retrieving a file version by its URL."""
    user = file_version.user
    api_client.force_authenticate(user=user)
    response = api_client.get(reverse("get_document_by_url", kwargs={"url": file_version.url}))
    assert response.status_code == status.HTTP_200_OK
    assert response["Content-Disposition"].startswith("attachment")


@pytest.mark.django_db
def test_get_file_version_by_cas(api_client, file_version):
    """Test retrieving a file version by its CAS URL."""
    user = file_version.user
    api_client.force_authenticate(user=user)
    response = api_client.get(reverse("get_document_by_cas_url", kwargs={"cas_url": file_version.url}))
    assert response.status_code == status.HTTP_200_OK
    assert response["Content-Disposition"].startswith("attachment")


@pytest.mark.django_db
def test_logout(api_client, user):
    """Test user logout functionality."""
    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    response = api_client.post(reverse("logout"))
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Token.objects.filter(key=token.key).exists()


@pytest.mark.django_db
def test_duplicate_file_upload(api_client, user):
    """Test uploading the same file twice to check CAS validation."""
    api_client.force_authenticate(user=user)
    content = ContentFile(b"Sample file content", name="sample.txt")
    file_data = {
        "file_name": "sample.txt",
        "file": content,
        "url": "test-url",
    }

    # Upload the file for the first time
    response_1 = api_client.post("/api/file_versions/", file_data, format="multipart")
    assert response_1.status_code == status.HTTP_201_CREATED

    # Check the CAS URL for the first upload
    cas_url_1 = response_1.data["cas_url"]

    # Upload the same file again
    response_2 = api_client.post("/api/file_versions/", file_data, format="multipart")
    assert response_2.status_code == status.HTTP_400_BAD_REQUEST

    file_versions = FileVersion.objects.filter(user=user)
    assert file_versions.count() == 1
    assert file_versions[0].cas_url == cas_url_1
