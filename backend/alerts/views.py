from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone as dj_timezone
from django.db.models import Q
from .models import AlertRule, Incident, IncidentStatus
from .serializers import AlertRuleSerializer, IncidentSerializer
from .evaluator import AlertEvaluator
from core.permissions import IsAdminOrReadOnly, IsAdminUserOnly
from core.models import AuditLog

class AlertRuleViewSet(viewsets.ModelViewSet):
    queryset = AlertRule.objects.all()
    serializer_class = AlertRuleSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        rule = serializer.save()
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='ALERT_RULE_CREATE',
            target_type='alert_rule',
            target_id=str(rule.id),
            details={'rule_name': rule.name, 'metric': rule.metric, 'threshold': rule.threshold},
            ip_address=self.request.META.get('REMOTE_ADDR')
        )

    def perform_update(self, serializer):
        rule = serializer.save()
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='ALERT_RULE_UPDATE',
            target_type='alert_rule',
            target_id=str(rule.id),
            details={'rule_name': rule.name, 'enabled': rule.enabled},
            ip_address=self.request.META.get('REMOTE_ADDR')
        )

    def perform_destroy(self, instance):
        rule_id = instance.id
        rule_name = instance.name
        instance.delete()
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='ALERT_RULE_DELETE',
            target_type='alert_rule',
            target_id=str(rule_id),
            details={'rule_name': rule_name},
            ip_address=self.request.META.get('REMOTE_ADDR')
        )


class IncidentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IncidentSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Incident.objects.all().select_related('rule', 'container', 'resolved_by')

        status_param = self.request.query_params.get('status')
        if status_param and status_param != 'all':
            qs = qs.filter(status__iexact=status_param)

        severity_param = self.request.query_params.get('severity')
        if severity_param:
            qs = qs.filter(severity__iexact=severity_param)

        container_param = self.request.query_params.get('container') or self.request.query_params.get('container_id')
        if container_param:
            qs = qs.filter(
                Q(container__id=container_param) |
                Q(container__container_id__istartswith=container_param) |
                Q(container__name__icontains=container_param)
            )

        return qs.order_by('-last_seen')

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUserOnly])
    def resolve(self, request, pk=None):
        incident = self.get_object()
        now = dj_timezone.now()
        note = request.data.get('note', 'Manually resolved by administrator')

        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = now
        incident.resolved_by = request.user if request.user.is_authenticated else None
        incident.resolution_note = note
        incident.save(update_fields=['status', 'resolved_at', 'resolved_by', 'resolution_note'])

        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action='INCIDENT_RESOLVE',
            target_type='incident',
            target_id=str(incident.id),
            details={'rule_name': incident.rule.name, 'container': incident.container.name, 'note': note},
            ip_address=request.META.get('REMOTE_ADDR')
        )

        return Response({
            "status": "success",
            "message": f"Incident #{incident.id} marked as resolved."
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUserOnly])
    def evaluate(self, request):
        evaluator = AlertEvaluator()
        summary = evaluator.evaluate_all()
        return Response(summary)
