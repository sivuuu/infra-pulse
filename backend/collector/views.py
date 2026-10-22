from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .runner import CollectorRunner
from core.permissions import IsAdminOrReadOnly

class CollectorTriggerView(APIView):
    """Trigger on-demand collector cycle."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        runner = CollectorRunner()
        result = runner.run_cycle()
        return Response(result, status=status.HTTP_200_OK if result.get('status') == 'success' else status.HTTP_200_OK)
