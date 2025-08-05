from rest_framework import permissions
from rest_framework.permissions import BasePermission

from ..models import FileShare, FileVersion


class IsOwnerOrReadOnly(BasePermission):
    """
    Permission class allowing read permissions for any authenticated user,
    but write permissions only for owners.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        return obj.user == request.user


class IsFileOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a file version to access or modify it.
    """

    def has_permission(self, request, view):
        # Only apply this permission to create actions
        if view.action == "create":
            file_version_id = request.data.get("file_version")
            if not file_version_id:
                return False
            file_version = FileVersion.objects.filter(id=file_version_id, user=request.user).exists()
            return file_version
        return True


class IsOwnerOrShared(BasePermission):
    """
    Permission class that grants read permissions to owners and users for whom the
    file version has been shared. Write permissions are granted only to the owner or
    shared users with 'can_edit' set to True.
    """

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, FileVersion):
            # Allow access if the request user is the owner
            if obj.user == request.user:
                return True
            # Check if the file has been shared with the user
            share_entry = FileShare.objects.filter(file_version=obj, shared_with=request.user).first()
            if share_entry:
                # Allow read-only access to a shared user
                if request.method in ["GET", "HEAD", "OPTIONS"]:
                    return True
                # Allow write access if can_edit is True
                if request.method in ["POST", "PUT", "PATCH"] and share_entry.can_edit:
                    return True
                # Allow delete access if can_delete is True
                if request.method in ["DELETE"] and share_entry.can_delete:
                    return True
        return False
