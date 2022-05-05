from audioop import add
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from rest_framework import serializers

from .exceptions import MetamaskWalletExistsError
from .models import MetamaskWallet


User = get_user_model()


class MetamaskWalletSerializer(serializers.Serializer):
    """Serializer for metamask."""

    wallet_address = serializers.CharField(
                            required=True,
                            error_messages={
                                'blank': "Адрес кошелька не может быть пустым.",
                                'required': "Поле 'адрес кошелька' отсутствует."
                                })

    def validate_wallet_address(self, wallet_address):
        try:
            address = MetamaskWallet.objects.get(wallet_address=wallet_address)
        except ObjectDoesNotExist:
            address = None
        if address:
            raise MetamaskWalletExistsError(
                    'Такой кошелек уже привязан к аккаунту.'
                    )
        return wallet_address
