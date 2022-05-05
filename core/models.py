from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class MetamaskWallet(models.Model):
    """Metamask wallet binded to user account"""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    wallet_address = models.CharField(max_length=128, unique=True)
