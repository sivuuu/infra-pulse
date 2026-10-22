import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from core.models import UserProfile, Role
from alerts.models import AlertRule, MetricType, ConditionOperator, Severity

@pytest.mark.django_db
def test_admin_vs_operator_permissions():
    client = APIClient()

    # Create admin
    admin = User.objects.create_user(username='admin_test', password='password123', is_staff=True)
    UserProfile.objects.create(user=admin, role=Role.ADMIN)

    # Create operator (read-only)
    operator = User.objects.create_user(username='operator_test', password='password123', is_staff=False)
    UserProfile.objects.create(user=operator, role=Role.OPERATOR)

    rule_payload = {
        "name": "Operator Rule Attempt",
        "metric": MetricType.CPU_PERCENT,
        "condition": ConditionOperator.GT,
        "threshold": 90.0,
        "severity": Severity.WARNING
    }

    # 1. Unauthenticated or Operator cannot create alert rules
    client.force_authenticate(user=operator)
    res_operator = client.post('/api/alerts/rules/', rule_payload, format='json')
    assert res_operator.status_code == 403

    # 2. Admin can create alert rules
    client.force_authenticate(user=admin)
    res_admin = client.post('/api/alerts/rules/', rule_payload, format='json')
    assert res_admin.status_code == 201

    # 3. Operator can read rules
    client.force_authenticate(user=operator)
    res_get = client.get('/api/alerts/rules/')
    assert res_get.status_code == 200
    assert len(res_get.data['results']) >= 1
