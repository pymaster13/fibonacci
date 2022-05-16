from django.core.management.base import BaseCommand, CommandError
from apscheduler.schedulers.background import BlockingScheduler
import pytz

from apscheduler.triggers.cron import CronTrigger

from core.periodic_tasks import (periodically_run_job,
                                 periodically_run_job_2)


scheduler = BlockingScheduler(timezone=pytz.UTC)


class Command(BaseCommand):
    help = 'Run blocking scheduler to create periodical tasks'

    def handle(self, *args, **options):
        print('Preparing scheduler')

        cron = CronTrigger(hour='*', minute='*', second='*/30', timezone=pytz.UTC)
        scheduler.add_job(periodically_run_job, cron)
        scheduler.add_job(periodically_run_job_2, cron)
        print('Start scheduler')
        scheduler.start()
