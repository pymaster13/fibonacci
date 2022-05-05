import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, Group, Permission
from django.core.mail import send_mail  
from django.core.validators import EmailValidator
from django.db import models

from .managers import UserManager
from config.settings import EMAIL_HOST_USER

class TgAccount(models.Model):
    """Telegram account for confirming account during registration"""

    tg_nickname = models.CharField(max_length=128,
                                         unique=True,
                                         verbose_name='Telegram nickname')
    is_confirmed = models.BooleanField(default=False,
                                       verbose_name='Confirmed')


class TgCode(models.Model):
    """Telegram code for confirming account during registration"""

    tg_account = models.ForeignKey(TgAccount, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created = models.DateTimeField(auto_now_add=True)


class User(AbstractBaseUser, PermissionsMixin):
    """Overriding django user model."""
    email = models.CharField(max_length=128,
                             unique=True,
                             verbose_name='Email',
                             validators=[EmailValidator])
    first_name = models.CharField(max_length=128,
                                  null=True,
                                  verbose_name='First name')
    last_name = models.CharField(max_length=128,
                                 null=True,
                                 verbose_name='Last name')

    telegram = models.OneToOneField(TgAccount, on_delete=models.CASCADE,
                                    verbose_name='Telegram account', null=True)

    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    groups = models.ManyToManyField(Group,
                                    related_name='account_groups',
                                    verbose_name='Groups', null=True,
                                    blank=True)
    user_permissions = models.ManyToManyField(Permission,
                                              related_name='account_perms',
                                              verbose_name='Permissions',
                                              null=True, blank=True)
    invite_code = models.UUIDField(default=uuid.uuid4,
                                   editable=False,
                                   unique=True)
    can_invite = models.BooleanField(default=False)
    inviter = models.OneToOneField('self',
                                   on_delete=models.SET_NULL,
                                   blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
