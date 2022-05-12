import uuid

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, Group, Permission
from django.core.validators import EmailValidator
from django.db import models

from .managers import UserManager


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
    inviter = models.ForeignKey('self',
                                on_delete=models.SET_NULL,
                                default=None,
                                blank=True,
                                null=True)
    balance = models.FloatField(default=0.0)
    line = models.IntegerField(default=1)
    permanent_place = models.IntegerField(null=True)
    hold = models.FloatField(default=0.0)

    STATUSES = [
        ('A', 'Active'),
        ('P', 'Passive'),
        ('N', 'NotActive'),
    ]

    status = models.CharField(
        max_length=1,
        choices=STATUSES,
        default='N',
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    @staticmethod
    def retrieve_all_user_partners(user, partners=None, to_check=None,
                                   active=0, passive=0, nonactive=0):
        if not partners and not to_check:
            partners = {}
            to_check = []

        invited_users = User.objects.filter(inviter=user)

        if invited_users or to_check:
            if invited_users:
                to_check.extend(invited_users)

            next_user = to_check.pop()

            if not partners.get(next_user.line):
                partners[next_user.line] = []
            partners[next_user.line].append(next_user.as_json())

            if next_user.status == 'A':
                active += 1
            elif next_user.status == 'P':
                passive += 1
            else:
                nonactive += 1

            return User.retrieve_all_user_partners(next_user, partners,
                                                   to_check, active,
                                                   passive, nonactive)

        return {'partners': partners,
                'stats': {
                            'active': active,
                            'passive': passive,
                            'nonactive': nonactive,
                            }
                }

    @property
    def partners(self):
        partners = User.retrieve_all_user_partners(self)
        return partners

    @property
    def fio(self):
        if self.last_name:
            last_name = self.last_name.lower().capitalize()
        else:
            last_name = ''
        if self.first_name:
            first_name = self.first_name.lower().capitalize()[:1]
        else:
            first_name = ''
        return f'{last_name} {first_name}.'

    @property
    def full_status(self):
        if self.status == 'A':
            full_status = 'Активный партнер'
        elif self.status == 'P':
            full_status = 'Пассивный партнер'
        else:
            full_status = 'Неактивный партнер'
        return full_status

    def as_json(self):
        summ = sum([i.allocation for i in self.idoparticipant_set.all()])
        return {
            'email': self.email,
            'fio': self.fio,
            'status': self.status,
            'telegram': self.telegram.tg_nickname,
            'balance': self.balance,
            'line': self.line,
            'referal': self.partners,
            'ido': summ if summ else 0
        }


class GoogleAuth(models.Model):
    """Model Google 2fa."""

    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             verbose_name="User")
    token = models.CharField(max_length=255, verbose_name="Secret key")
    is_installed = models.BooleanField(default=False)

    class Meta:
        db_table = "google_auth"
        verbose_name = "Google Verification"
        verbose_name_plural = verbose_name
