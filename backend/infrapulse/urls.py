from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core.views import HealthView, ReadinessView, LoginView, LogoutView, MeView, AuditLogViewSet
from targets.views import HostTargetViewSet
from containers.views import ContainerViewSet
from metrics.views import MetricSummaryView, TimeSeriesMetricsView, PrometheusMetricsView
from logs.views import LogEntryViewSet, LogIngestView
from alerts.views import AlertRuleViewSet, IncidentViewSet
from collector.views import CollectorTriggerView

router = DefaultRouter()
router.register(r'targets', HostTargetViewSet, basename='target')
router.register(r'containers', ContainerViewSet, basename='container')
router.register(r'logs', LogEntryViewSet, basename='log')
router.register(r'alerts/rules', AlertRuleViewSet, basename='alert-rule')
router.register(r'alerts/incidents', IncidentViewSet, basename='incident')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Health & Readiness
    path('api/health/', HealthView.as_view(), name='health'),
    path('api/ready/', ReadinessView.as_view(), name='readiness'),

    # Prometheus Exposition
    path('metrics', PrometheusMetricsView.as_view(), name='prometheus-metrics'),

    # Auth
    path('api/auth/login/', LoginView.as_view(), name='auth-login'),
    path('api/auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('api/auth/me/', MeView.as_view(), name='auth-me'),

    # Collector on-demand trigger
    path('api/collector/trigger/', CollectorTriggerView.as_view(), name='collector-trigger'),

    # Metrics & Dashboard Stats
    path('api/metrics/summary/', MetricSummaryView.as_view(), name='metrics-summary'),
    path('api/dashboard/stats/', MetricSummaryView.as_view(), name='dashboard-stats'),
    path('api/metrics/time-series/', TimeSeriesMetricsView.as_view(), name='metrics-time-series'),

    # Log ingestion
    path('api/logs/ingest/', LogIngestView.as_view(), name='logs-ingest'),

    # REST Router
    path('api/', include(router.urls)),
]
