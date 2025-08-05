import pytest

from propylon_document_manager.file_versions.models import FileShare, FileVersion, User
from .factories import FileShareFactory, FileVersionFactory, UserFactory


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory()


@pytest.fixture
def file_version(db) -> FileVersion:
    """Fixture to create a FileVersion instance."""
    return FileVersionFactory()


@pytest.fixture
def file_share(db) -> FileShare:
    """Fixture to create a FileVersion instance."""
    return FileShareFactory()
