import os
from hashlib import md5

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField, EmailField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from propylon_document_manager.utils.validators import validate_file_extension


class User(AbstractUser):
    """
    Default custom user model for Propylon Document Manager.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore
    last_name = None  # type: ignore
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.id})


class FileVersion(models.Model):
    file_name = models.CharField(max_length=512, null=True, blank=True, default=None)
    version_number = models.fields.PositiveSmallIntegerField(default=0)
    file = models.FileField(
        upload_to="files/", null=True, blank=True, default=None, validators=[validate_file_extension]
    )
    file_extension = models.CharField(max_length=10, null=True, blank=True)
    url = models.CharField(max_length=512, null=True, blank=True, default=None)
    cas_url = models.CharField(max_length=128, unique=True, null=True, blank=True)  # CAS unique identifier

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.file:
            _, extension = os.path.splitext(self.file.name)
            self.file_extension = extension.lstrip(".").lower()
            self.cas_url = md5(self.file.read()).hexdigest()  # Generate CAS URL

            # Get the latest version number for the same URL
            latest_version = FileVersion.objects.filter(url=self.url).order_by("-version_number").first()
            if latest_version:
                self.version_number = latest_version.version_number + 1
            else:
                self.version_number = 1
        super().save(*args, **kwargs)


class FileShare(models.Model):
    file_version = models.ForeignKey(FileVersion, on_delete=models.CASCADE)
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("file_version", "shared_with")
