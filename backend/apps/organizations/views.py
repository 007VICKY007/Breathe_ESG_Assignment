from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Create organization + first admin user (prototype bootstrap)."""

    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class MeView(APIView):
    """Return the authenticated user's profile and tenant context."""

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class CustomTokenObtainPairView(TokenObtainPairView):
    """JWT login — username/password; user must belong to an organization."""

    permission_classes = [permissions.AllowAny]
