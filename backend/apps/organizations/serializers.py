from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Organization

User = get_user_model()


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "slug")


class UserSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "organization",
        )
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    """Bootstrap registration — creates org + admin user (prototype only)."""

    organization_name = serializers.CharField(max_length=255)
    organization_slug = serializers.SlugField(max_length=100)
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_organization_slug(self, value):
        if Organization.objects.filter(slug=value).exists():
            raise serializers.ValidationError("Organization slug already exists.")
        return value

    def create(self, validated_data):
        org = Organization.objects.create(
            name=validated_data["organization_name"],
            slug=validated_data["organization_slug"],
        )
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            organization=org,
            role=User.Role.ADMIN,
        )
        return user
