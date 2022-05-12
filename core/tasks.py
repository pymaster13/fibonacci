import dramatiq

"""
Run dramatiq workers - "dramatiq core.tasks"
"""


@dramatiq.actor
def process(string):
    """Very simple task for demonstrating purpose."""
    print('Start my long-running task')
    print(string)
