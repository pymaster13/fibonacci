import base64
import io
from datetime import datetime as dt, timezone
from random import randint
from math import ceil
from typing import Tuple

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
import pyotp
from qrcode import QRCode, constants

from .models import TgCode
from .exceptions import RetrievePermissionsError
from config.settings import EMAIL_HOST_USER


User = get_user_model()


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


def generate_google_qrcode(token, email):
    """Help function for generating code Google Authenticator."""
    data = pyotp.totp.TOTP(token).provisioning_uri(
                                                name=email,
                                                issuer_name='Fibonacci'
                                                )
    qr = QRCode(error_correction=constants.ERROR_CORRECT_L,
                version=1,
                box_size=6,
                border=4)
    try:
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image()

        byte_in = io.BytesIO()
        img.save(byte_in, format='PNG')
        byte_out = byte_in.getvalue()
        enc_bytes = base64.b64encode(byte_out)

        return str(enc_bytes)[2:-1]

    except Exception as e:
        print(e)
        return


def verify_google_code(token, code):
    """Help function to verify code Google Authenticator."""
    t = pyotp.TOTP(token)
    result = t.verify(code)
    return result if result is True else False


def retrieve_permissions(user):
    """Help function to retrieve user permissions."""
    permissions_db = ("ido", "transaction", "user", "news", 'statistics')
    try:
        permissions = set()
        for perm in user.user_permissions.all():
            name = perm.codename.split('_')[1]
            if name in permissions_db:
                permissions.add(name)

        if user.is_staff or user.is_superuser:
            permissions.add('admin')

        return permissions

    except Exception as e:
        print(e)
        raise RetrievePermissionsError("Ошибка получения прав пользователя.")


def paginate(items: list, objects_on_page: int, current_page: int) -> Tuple[list, int, int]:
    if not items:
        return [], 1, 1

    count_pages = ceil(len(items) / objects_on_page)

    if current_page <= 0:
        return items[:objects_on_page], count_pages, 1

    if current_page > count_pages:
        return [], count_pages, current_page
    elif current_page == count_pages:
        return items[(current_page-1)*objects_on_page:], count_pages, current_page
    else:
        return (items[(current_page-1)*objects_on_page:current_page*objects_on_page],
               count_pages,
               current_page)
