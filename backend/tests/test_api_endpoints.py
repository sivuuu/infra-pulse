import pytest
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_health_and_readiness_endpoints():
    client = APIClient()
    res_health = client.get('/api/health/')
    assert res_health.status_code == 200
    assert res_health.data['status'] in ('healthy', 'degraded')
    assert res_health.data['database'] == 'connected'

    res_ready = client.get('/api/ready/')
    assert res_ready.status_code == 200
    assert res_ready.data['status'] == 'ready'

@pytest.mark.django_db
def test_metrics_summary_and_prometheus_exposition():
    client = APIClient()
    res_summary = client.get('/api/metrics/summary/')
    assert res_summary.status_code == 200
    assert 'containers' in res_summary.data
    assert 'system_metrics' in res_summary.data
    assert 'alerts' in res_summary.data

    res_prom = client.get('/metrics')
    assert res_prom.status_code == 200
    assert 'container_cpu_usage_percent' in res_prom.content.decode('utf-8') or 'infrapulse_target_up' in res_prom.content.decode('utf-8')

@pytest.mark.django_db
def test_containers_list_and_filter():
    client = APIClient()
    res = client.get('/api/containers/')
    assert res.status_code == 200
    assert 'results' in res.data
