from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from datetime import datetime
from .models import LogEntry
from .serializers import LogEntrySerializer
from .scrubber import sanitize_log_message
from containers.models import Container

class LogEntryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LogEntrySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = LogEntry.objects.all().select_related('container')

        container_param = self.request.query_params.get('container') or self.request.query_params.get('container_id')
        if container_param:
            qs = qs.filter(
                Q(container__id=container_param) |
                Q(container__container_id__istartswith=container_param) |
                Q(container__name__icontains=container_param)
            )

        level_param = self.request.query_params.get('level')
        if level_param:
            qs = qs.filter(level__iexact=level_param)

        search_param = self.request.query_params.get('search')
        if search_param:
            qs = qs.filter(message__icontains=search_param)

        incident_param = self.request.query_params.get('incident_id')
        if incident_param:
            qs = qs.filter(related_incident_id=incident_param)

        since_param = self.request.query_params.get('since')
        if since_param:
            try:
                dt_since = datetime.fromisoformat(since_param.replace("Z", "+00:00"))
                qs = qs.filter(timestamp__gte=dt_since)
            except Exception:
                pass

        until_param = self.request.query_params.get('until')
        if until_param:
            try:
                dt_until = datetime.fromisoformat(until_param.replace("Z", "+00:00"))
                qs = qs.filter(timestamp__lte=dt_until)
            except Exception:
                pass

        return qs.order_by('-timestamp')


class LogIngestView(APIView):
    """
    Controlled internal ingestion endpoint for restricted log collectors.
    Automatically scrubs credentials and sensitive tokens.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        entries = request.data if isinstance(request.data, list) else [request.data]
        created_count = 0

        for item in entries:
            container_id = item.get('container_id')
            raw_msg = item.get('message', '')
            if not container_id or not raw_msg:
                continue

            container = Container.objects.filter(
                Q(container_id__istartswith=container_id) | Q(name=container_id)
            ).first()
            if not container:
                continue

            sanitized, was_redacted = sanitize_log_message(raw_msg)
            ts = item.get('timestamp')
            parsed_ts = datetime.utcnow()
            if ts:
                try:
                    parsed_ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except Exception:
                    pass

            LogEntry.objects.create(
                container=container,
                timestamp=parsed_ts,
                level=item.get('level', 'INFO').upper(),
                source=item.get('source', 'stdout'),
                message=sanitized,
                raw_message="***REDACTED***" if was_redacted else sanitized,
                is_sensitive_redacted=was_redacted,
                related_incident_id=item.get('related_incident_id')
            )
            created_count += 1

        return Response({"status": "success", "ingested": created_count}, status=status.HTTP_201_CREATED)
