from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class VIPUser(models.Model):
    """Model VIP User"""

    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             verbose_name="User")
    referal_profit = models.FloatField(null=True, blank=True,
                                       verbose_name="referal IDO income percent")
