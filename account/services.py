from datetime import datetime as dt, timezone
from random import randint

from .models import TgCode


def generate_code(tg_account):
    code = str(randint(1, 999999))
    while len(code) < 6:
        code = '0' + code

    tg_code = TgCode(tg_account=tg_account, code=code)
    tg_code.save()

    return tg_code


def check_code_time(tg_code, limit):
    diff_time = dt.now(timezone.utc) - tg_code.created
    if diff_time.total_seconds() >= limit:
        return False

    return True
