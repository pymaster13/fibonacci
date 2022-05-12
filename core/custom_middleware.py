import dramatiq

from .periodic_tasks import _SCHEDULER


class AntiScheduleMiddleware(dramatiq.Middleware):
    def before_worker_boot(self, broker, worker):
        _SCHEDULER.shutdown()
