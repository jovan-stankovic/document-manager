from rest_framework import permissions
from rest_framework.permissions import BasePermission

from ..models import FileVersion


class IsOwnerOrReadOnly(BasePermission):
    """
    Permission class allowing read permissions for any authenticated user,
    but write permissions only for owners.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        return obj.user == request.user


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a file version to access or modify it.
    """

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, FileVersion):
            return obj.user == request.user
        return False
