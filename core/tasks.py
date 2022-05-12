import time

import dramatiq


@dramatiq.actor
def process_user_stats(string):
    """Very simple task for demonstrating purpose."""
    print('Start my long-running task')
    print(string)
