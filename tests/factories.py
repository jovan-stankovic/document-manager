from collections.abc import Sequence
from typing import Any

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from factory import Faker, post_generation, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker as FakerLib

from propylon_document_manager.file_versions.models import FileVersion

fake = FakerLib()


class UserFactory(DjangoModelFactory):
    email = Faker("email")
    name = Faker("name")

    @post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):
        password = (
            extracted
            if extracted
            else Faker(
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).evaluate(None, None, extra={"locale": None})
        )
        self.set_password(password)

    class Meta:
        model = get_user_model()
        django_get_or_create = ["email"]


class FileVersionFactory(DjangoModelFactory):
    file_name = Faker("file_name")
    version_number = Faker("random_int", min=0, max=10)
    file_extension = "txt"
    url = "test-file-url"
    cas_url = Faker("md5")  # Mimic CAS generation logic with Faker

    user = SubFactory(UserFactory)

    @post_generation
    def file(self, create: bool, extracted: Sequence[Any], **kwargs):
        """Add file content after creation."""
        if not create:
            return

        # Create a dummy file with content
        if extracted:
            self.file.save(extracted.file_name, extracted)
        else:
            file_content = fake.text(max_nb_chars=1024)
            content = ContentFile(file_content.encode("utf-8"))
            self.file.save(f"{self.file_name}.{self.file_extension}", content)

    class Meta:
        model = FileVersion
