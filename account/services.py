from datetime import datetime as dt, timezone
from random import randint
from django.core.mail import send_mail

from .models import TgCode
from config.settings import EMAIL_HOST_USER


def generate_code(tg_account):
    """Help function for generating code that is sended to Telegram."""
    code = str(randint(1, 999999))
    while len(code) < 6:
        code = '0' + code

    tg_code = TgCode(tg_account=tg_account, code=code)
    tg_code.save()

    return tg_code


def check_code_time(tg_code, limit):
    """Help function for checking code correctness."""
    diff_time = dt.now(timezone.utc) - tg_code.created
    if diff_time.total_seconds() >= limit:
        return False

    return True


def send_mail_message(token_obj):
    """Help function for sending mail."""
    head = "Восстановление пароля"
    ref = f"localhost:3000/password_reset?token={token_obj.key}"
    body = f"Для восстановления пароля перейдите по следующей ссылке: {ref}"
    from_mail = EMAIL_HOST_USER
    to_mail = [token_obj.user.email]

    # Message in terminal
    send_mail(head, body, from_mail, to_mail)
