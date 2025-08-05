from rest_framework import serializers

from ..models import FileShare, FileVersion, User


class FileVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileVersion
        fields = [
            "id",
            "file_name",
            "file_extension",
            "version_number",
            "file",
            "url",
            "cas_url",
            "created_at",
            "updated_at",
            "user",
        ]
        read_only_fields = ["id", "cas_url", "created_at", "updated_at", "user", "file_extension", "version_number"]

    def create(self, validated_data):
        request = self.context.get("request")
        return FileVersion.objects.create(user=request.user, **validated_data)


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "name", "email", "password"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField()


class FileShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileShare
        fields = ["id", "file_version", "shared_with", "can_edit", "can_delete"]
        read_only_fields = ["id", "created_at"]
