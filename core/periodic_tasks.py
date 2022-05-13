from .tasks import process, retreive_coins_cost


def periodically_run_job():

    """This task will be run by APScheduler. It can prepare some data and parameters and then enqueue background task."""
    print('TOKENS')
    process.send()


def periodically_run_job_2():

    """This task will be run by APScheduler. It can prepare some data and parameters and then enqueue background task."""
    print('COINS')
    retreive_coins_cost.send()
