import pytest
from django.core.files.base import ContentFile
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from propylon_document_manager.file_versions.models import FileShare, FileVersion, User
from tests.factories import FileShareFactory, UserFactory


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

    response = api_client.post(reverse("api:file-versions-list"), file_data, format="multipart")
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
    response_1 = api_client.post(reverse("api:file-versions-list"), file_data, format="multipart")
    assert response_1.status_code == status.HTTP_201_CREATED

    # Check the CAS URL for the first upload
    cas_url_1 = response_1.data["cas_url"]

    # Upload the same file again
    response_2 = api_client.post(reverse("api:file-versions-list"), file_data, format="multipart")
    assert response_2.status_code == status.HTTP_400_BAD_REQUEST

    file_versions = FileVersion.objects.filter(user=user)
    assert file_versions.count() == 1
    assert file_versions[0].cas_url == cas_url_1


@pytest.mark.django_db
def test_file_share_creation(api_client, file_version):
    """Test creating a file share for a file version."""
    owner = file_version.user
    shared_user = UserFactory()
    api_client.force_authenticate(user=owner)

    share_data = {
        "file_version": file_version.id,
        "shared_with": shared_user.id,
        "can_edit": True,
        "can_delete": False,
    }
    response = api_client.post(reverse("api:file-shares-list"), share_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert FileShare.objects.filter(file_version=file_version, shared_with=shared_user).exists()


@pytest.mark.django_db
def test_non_owner_file_share_creation(api_client, file_version):
    """
    Test that a user who is not the owner of a FileVersion cannot share it with others.
    Expect a 403 Forbidden response.
    """
    # Create a user who is not the owner of the file_version
    non_owner_user = UserFactory()
    # Authenticate as a non-owner user
    api_client.force_authenticate(user=non_owner_user)

    # Attempt to create a share with another user
    another_user = UserFactory()
    share_data = {
        "file_version": file_version.id,
        "shared_with": another_user.id,
        "can_edit": True,
        "can_delete": False,
    }

    response = api_client.post(reverse("api:file-shares-list"), share_data)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert not FileShare.objects.filter(file_version=file_version, shared_with=another_user).exists()


@pytest.mark.django_db
def test_file_share_permissions(api_client, file_version):
    """Test permissions based on file share configuration."""
    owner = file_version.user
    shared_user = UserFactory()
    api_client.force_authenticate(user=owner)

    share_data = {
        "file_version": file_version.id,
        "shared_with": shared_user.id,
        "can_edit": True,
        "can_delete": True,
    }
    api_client.post(reverse("api:file-shares-list"), share_data)

    # Test shared user can view the file version
    api_client.force_authenticate(user=shared_user)
    response = api_client.get(reverse("api:file-versions-detail", kwargs={"id": file_version.id}))
    assert response.status_code == status.HTTP_200_OK

    # Test shared user can edit the file version
    edit_data = {"file_name": "updated_name"}
    response = api_client.patch(reverse("api:file-versions-detail", kwargs={"id": file_version.id}), edit_data)
    assert response.status_code == status.HTTP_200_OK

    # Test shared user can delete the file version
    response = api_client.delete(reverse("api:file-versions-detail", kwargs={"id": file_version.id}))
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_file_share_no_edit_permission(api_client, file_version):
    """Test user without edit permission cannot modify the file version."""
    shared_user = UserFactory()
    api_client.force_authenticate(user=file_version.user)

    # Create a file share without edit permissions.
    FileShareFactory(file_version=file_version, shared_with=shared_user, can_edit=False, can_delete=False)

    api_client.force_authenticate(user=shared_user)
    edit_data = {"file_name": "attempted_update"}
    response = api_client.patch(reverse("api:file-versions-detail", kwargs={"id": file_version.id}), edit_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_file_share_no_delete_permission(api_client, file_version):
    """Test user without delete permission cannot delete the file version."""
    shared_user = UserFactory()
    api_client.force_authenticate(user=file_version.user)

    # Create a file share without delete permissions.
    FileShareFactory(file_version=file_version, shared_with=shared_user, can_edit=True, can_delete=False)

    api_client.force_authenticate(user=shared_user)
    response = api_client.delete(reverse("api:file-versions-detail", kwargs={"id": file_version.id}))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_permission_revocation(api_client, file_version):
    """Test revocation of edit and delete permissions."""
    owner = file_version.user
    shared_user = UserFactory()
    api_client.force_authenticate(user=owner)

    share_data = {
        "file_version": file_version.id,
        "shared_with": shared_user.id,
        "can_edit": True,
        "can_delete": True,
    }
    response = api_client.post(reverse("api:file-shares-list"), share_data)
    assert response.status_code == status.HTTP_201_CREATED

    # Revoke permissions
    revoke_data = {
        "can_edit": False,
        "can_delete": False,
    }
    file_share = FileShare.objects.get(file_version=file_version, shared_with=shared_user)
    api_client.patch(reverse("api:file-shares-detail", kwargs={"pk": file_share.id}), revoke_data)

    # Verify permissions are revoked
    api_client.force_authenticate(user=shared_user)
    response = api_client.patch(
        reverse("api:file-versions-detail", kwargs={"id": file_version.id}), {"file_name": "invalid_update"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    response = api_client.delete(reverse("api:file-versions-detail", kwargs={"id": file_version.id}))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_overwriting_file_share_permissions(api_client, file_version):
    """Test overwriting permissions on existing file share does not create duplicate."""
    owner = file_version.user
    shared_user = UserFactory()
    api_client.force_authenticate(user=owner)

    share_data = {
        "file_version": file_version.id,
        "shared_with": shared_user.id,
        "can_edit": False,
        "can_delete": False,
    }
    api_client.post(reverse("api:file-shares-list"), share_data)

    # Update permissions
    overwrite_data = {
        "can_edit": True,
        "can_delete": True,
    }
    file_share = FileShare.objects.get(file_version=file_version, shared_with=shared_user)
    response = api_client.patch(reverse("api:file-shares-detail", kwargs={"pk": file_share.id}), overwrite_data)
    assert response.status_code == status.HTTP_200_OK
    assert FileShare.objects.filter(file_version=file_version, shared_with=shared_user).count() == 1

    # Verify updated permissions
    api_client.force_authenticate(user=shared_user)
    response = api_client.delete(reverse("api:file-versions-detail", kwargs={"id": file_version.id}))
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_file_share_removal(api_client, file_version):
    """Test removal of a file share leads to permission loss."""
    owner = file_version.user
    shared_user = UserFactory()
    api_client.force_authenticate(user=owner)

    share_data = {
        "file_version": file_version.id,
        "shared_with": shared_user.id,
        "can_edit": True,
        "can_delete": True,
    }
    response = api_client.post(reverse("api:file-shares-list"), share_data)
    assert response.status_code == status.HTTP_201_CREATED

    # Remove the share
    file_share = FileShare.objects.get(file_version=file_version, shared_with=shared_user)
    api_client.delete(reverse("api:file-shares-detail", kwargs={"pk": file_share.id}))
    assert not FileShare.objects.filter(file_version=file_version, shared_with=shared_user).exists()

    # Verify loss of permissions
    api_client.force_authenticate(user=shared_user)
    response = api_client.get(reverse("api:file-versions-detail", kwargs={"id": file_version.id}))
    assert response.status_code == status.HTTP_403_FORBIDDEN
