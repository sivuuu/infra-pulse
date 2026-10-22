import pytest
from collector.runner import CollectorRunner
from runtime.mock_adapter import MockContainerRuntimeAdapter
from targets.models import HostTarget, TargetStatus
from containers.models import Container, ContainerState
from metrics.models import MetricSample

@pytest.mark.django_db
def test_collector_cycle_with_mock_adapter():
    runner = CollectorRunner(target_name="mock-integration-target")
    # Inject mock adapter with alive status
    runner.adapter = MockContainerRuntimeAdapter(is_alive=True)

    result = runner.run_cycle()
    assert result['status'] == 'success'
    assert result['containers_monitored'] == 3
    assert result['metrics_collected'] >= 2

    target = HostTarget.objects.get(name="mock-integration-target")
    assert target.status == TargetStatus.REACHABLE

    # Check containers saved
    assert Container.objects.filter(target=target).count() == 3

    # Check unavailable metric distinction for exited container
    exited_cont = Container.objects.get(container_id="mock_worker_03")
    sample = MetricSample.objects.filter(container=exited_cont).order_by('-timestamp').first()
    assert sample.is_available is False
    assert sample.cpu_percent is None

@pytest.mark.django_db
def test_collector_unreachable_host_handling():
    runner = CollectorRunner(target_name="mock-unreachable-target")
    # Inject unreachable mock adapter
    runner.adapter = MockContainerRuntimeAdapter(is_alive=False)

    result = runner.run_cycle()
    assert result['status'] == 'unreachable'

    target = HostTarget.objects.get(name="mock-unreachable-target")
    assert target.status == TargetStatus.UNREACHABLE
    assert "refused" in target.error_message.lower() or "unreachable" in target.error_message.lower()
