from audioop import add
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from rest_framework import serializers

from core.models import Address
from .exceptions import MetamaskWalletExistsError


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
            address = Address.objects.get(address=wallet_address)
        except ObjectDoesNotExist:
            address = None
        if address:
            raise MetamaskWalletExistsError(
                    'Такой кошелек уже привязан.'
                    )
        return wallet_address


class UserReserveSerializer(serializers.Serializer):
    """Serializer for user reserve."""

    amount = serializers.FloatField(required=True,
                                    error_messages={
                                        'blank': "Сумма не может быть пустой.",
                                        'required': "Поле 'сумма' отсутствует."
                                        })
