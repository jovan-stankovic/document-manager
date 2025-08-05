from django.db.utils import IntegrityError
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from drf_spectacular.utils import OpenApiParameter
from rest_framework import status
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsOwner
from .serializers import FileVersionSerializer, LoginSerializer, TokenSerializer
from .serializers import UserSerializer
from ..models import FileVersion


class FileVersionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = FileVersionSerializer
    lookup_field = "id"

    def get_queryset(self):
        return FileVersion.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "format": "binary"},
                    "file_name": {"type": "string"},
                    "url": {"type": "string"},
                },
            }
        },
        responses={201: FileVersionSerializer, 400: "Bad Request"},
        description=(
            "Create a new file version. Authenticated users can upload a file and provide "
            "an optional filename and URL. Returns 400 if the file was already uploaded."
        ),
    )
    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response("You have already uploaded this file.", status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={200: FileVersionSerializer(many=True)},
        description=(
            "Retrieve a list of all file versions belonging to the authenticated user. "
            "Each version's details are returned."
        ),
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        responses={200: FileVersionSerializer},
        description=(
            "Retrieve details of a specific file version identified by 'id'. This method "
            "ensures that the user owns the requested version."
        ),
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=FileVersionSerializer,
        responses={200: FileVersionSerializer},
        description=(
            "Update the details of an existing file version specified by 'id'. The user must "
            "be the owner to modify the file."
        ),
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        request=FileVersionSerializer,
        responses={200: FileVersionSerializer},
        description=(
            "Modify parts of an existing file version specified by 'id'. Partial updates "
            "are allowed to fields like file name or URL."
        ),
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        responses={204: None},
        description=(
            "Delete a file version identified by 'id'. The authenticated user must own the "
            "file version they wish to delete."
        ),
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class GetFileVersionByURL(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="revision",
                description="Optional version number",
                required=False,
                type=int,
            ),
        ],
        responses={200: FileResponse},
        description=(
            "Retrieve a specific file version by its URL. Optionally supply a revision number "
            "to get that version; otherwise, the latest version is returned. Requires ownership of the file."
        ),
    )
    def get(self, request, url):
        queryset = FileVersion.objects.filter(url=url, user=request.user)
        revision = request.query_params.get("revision", None)

        if revision and revision.isdigit():
            specific_version = get_object_or_404(queryset, version_number=revision)
        else:
            specific_version = queryset.order_by("-version_number").first()

        if specific_version:
            response = FileResponse(specific_version.file.open(), as_attachment=True)
            revision_tag = revision if revision else "latest"
            response["Content-Disposition"] = (
                f'attachment; filename="{specific_version.file_name}-{revision_tag}.{specific_version.file_extension}"'
            )

            return response

        return Response({"detail": "No document versions found for this URL"}, status=status.HTTP_404_NOT_FOUND)


class GetFileVersionByCAS(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    @extend_schema(
        responses={200: FileResponse},
        description=(
            "Retrieve a file version by its CAS (Content-Addressable Storage) URL. The file "
            "must belong to the authenticated user."
        ),
    )
    def get(self, request, cas_url):
        file_version = get_object_or_404(FileVersion, cas_url=cas_url, user=request.user)

        if file_version.file:
            response = FileResponse(file_version.file.open(), as_attachment=True)
            response["Content-Disposition"] = (
                f'attachment; filename="{file_version.file_name}-version'
                f'{file_version.version_number}.{file_version.file_extension}"'
            )
            return response

        return Response({"detail": "No document found for this CAS URL"}, status=status.HTTP_404_NOT_FOUND)


class UserRegistrationView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=UserSerializer,
        responses={201: UserSerializer},
        description=(
            "Register a new user by providing required details. Returns the newly "
            "registered user's information upon success."
        ),
    )
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomLoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={200: TokenSerializer},
        description=(
            "Authenticate a user using their username and password to obtain an "
            "authentication token for future requests."
        ),
    )
    def post(self, request, *args, **kwargs):
        return obtain_auth_token(request._request)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={204: None},
        description=(
            "Log out the current user by deleting their authentication token. Upon success, " "returns no content."
        ),
    )
    def post(self, request):
        try:
            token = Token.objects.get(user=request.user)
            token.delete()
        except Token.DoesNotExist:
            pass

        # Return response with no content status
        return Response(status=status.HTTP_204_NO_CONTENT)
