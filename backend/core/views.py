from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import connection
from .models import AuditLog, UserProfile, Role
from .serializers import UserSerializer, AuditLogSerializer
from .permissions import IsAdminOrReadOnly
from targets.models import HostTarget
from containers.models import Container

class HealthView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        db_healthy = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as e:
            db_healthy = False

        targets = HostTarget.objects.all()
        targets_healthy = any(t.status == 'reachable' for t in targets) if targets.exists() else True

        is_healthy = db_healthy and targets_healthy
        return Response({
            "status": "healthy" if is_healthy else "degraded",
            "database": "connected" if db_healthy else "error",
            "targets_count": targets.count(),
            "containers_count": Container.objects.count(),
            "version": "1.0.0"
        }, status=status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE)

class ReadinessView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"status": "ready"}, status=status.HTTP_200_OK)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({"error": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({"error": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)

        login(request, user)
        # Ensure profile exists
        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': Role.ADMIN if user.is_superuser else Role.OPERATOR}
        )

        AuditLog.objects.create(
            user=user,
            action='USER_LOGIN',
            target_type='auth',
            target_id=str(user.id),
            details={'username': user.username},
            ip_address=request.META.get('REMOTE_ADDR')
        )

        serializer = UserSerializer(user)
        return Response({
            "message": "Login successful",
            "user": serializer.data
        })

class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if request.user.is_authenticated:
            AuditLog.objects.create(
                user=request.user,
                action='USER_LOGOUT',
                target_type='auth',
                target_id=str(request.user.id),
                details={'username': request.user.username},
                ip_address=request.META.get('REMOTE_ADDR')
            )
            logout(request)
        return Response({"message": "Logged out successfully"})

class MeView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            # Return demo/anonymous operator profile for initial inspection
            return Response({
                "authenticated": False,
                "user": {
                    "username": "anonymous_operator",
                    "role": "operator",
                    "is_superuser": False
                }
            })
        serializer = UserSerializer(request.user)
        return Response({
            "authenticated": True,
            "user": serializer.data
        })

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.AllowAny]
