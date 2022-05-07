import base64
import io
from datetime import datetime as dt, timezone
from random import randint

from django.contrib.auth.models import Permission
from django.core.mail import send_mail
import pyotp
from qrcode import QRCode, constants

from .exceptions import GrantPermissionsError
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


def grant_permissions(user, perms):
    """Help function to grant permissions to user"""
    try:
        actions = ('add', 'change', 'delete')
        permissions_db = ("ido", "transaction", "user", "news")
        result_perms = []

        for perm in perms:
            if perm in permissions_db:
                for action in actions:
                    codename = f'{action}_{perm}'
                    perm_obj = Permission.objects.get(codename=codename)
                    result_perms.append(perm_obj)

        if 'admin' in perms:
            user.is_staff = True
            user.is_superuser = True
        else:
            user.is_staff = False
            user.is_superuser = False

        if result_perms:
            user.user_permissions.set(result_perms)
        else:
            user.user_permissions.clear()

        user.save()

        return True

    except Exception as e:
        print(e)
        raise GrantPermissionsError("Ошибка предоставления прав пользователю.")
