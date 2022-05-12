import os

from apscheduler.schedulers.background import BackgroundScheduler
import pytz

from .tasks import process


_SCHEDULER = BackgroundScheduler(timezone=pytz.UTC)


def periodically_run_job():

    """This task will be run by APScheduler. It can prepare some data and parameters and then enqueue background task."""
    print('It is time to start the dramatiq task')
    process.send('123')
