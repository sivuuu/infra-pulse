import time
from django.core.management.base import BaseCommand
from collector.runner import CollectorRunner

class Command(BaseCommand):
    help = "Run container metrics and status collection cycle"

    def add_arguments(self, parser):
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Run continuously in background daemon loop'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=5,
            help='Interval in seconds between collection cycles in daemon mode'
        )

    def handle(self, *args, **options):
        runner = CollectorRunner()
        is_daemon = options['daemon']
        interval = options['interval']

        if not is_daemon:
            self.stdout.write(self.style.NOTICE("Running one-off collection cycle..."))
            res = runner.run_cycle()
            self.stdout.write(self.style.SUCCESS(f"Cycle completed: {res}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Starting InfraPulse Collector Daemon (poll interval: {interval}s)..."))
        try:
            while True:
                res = runner.run_cycle()
                self.stdout.write(f"[{res.get('timestamp')}] Status: {res.get('status')} | Containers: {res.get('containers_monitored', 0)} | Alerts: {res.get('alerts', {}).get('firing', 0)} firing")
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Collector daemon stopped by user."))
