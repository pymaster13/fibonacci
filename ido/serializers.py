from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework import serializers

from .exceptions import IDOExistsError, AllocationError, ManuallyChargeError
from .models import IDO
from account.exceptions import (EmailValidationError, UserDoesNotExists)


User = get_user_model()


class PureIDOSerializer(serializers.ModelSerializer):
    class Meta:
        model = IDO
        fields = '__all__'


class IDOSerializer(serializers.ModelSerializer):

    users = serializers.ListField(
                        child=serializers.CharField(),
                        required=False)
    allocations = serializers.ListField(
                        child=serializers.FloatField(),
                        required=False)

    class Meta:
        model = IDO
        fields = '__all__'


class ParticipateIDOSerializer(serializers.Serializer):

    ido = serializers.IntegerField(
                    required=True,
                    error_messages={
                        'blank': "IDO не может быть пустым."
                        })

    def validate(self, attrs):
        try:
            ido = IDO.objects.get(pk=attrs['ido'])
        except Exception:
            raise IDOExistsError('Указан некорректный идентификатор IDO.')

        return ido


class AddUserQueueSerializer(serializers.Serializer):

    ido = serializers.IntegerField(
                    required=True,
                    error_messages={
                        'blank': "IDO не может быть пустым."
                        })

    def validate(self, attrs):
        try:
            ido = IDO.objects.get(pk=attrs['ido'])
        except Exception:
            raise IDOExistsError('Указан некорректный идентификатор IDO.')

        if attrs.get('allocation', 0) < 0:
            raise AllocationError('Аллокация не может быть отрицательной.')

        return ido


class ChargeManuallySerializer(serializers.Serializer):
    ido = serializers.IntegerField(
                            required=True,
                            error_messages={
                                'blank': "Идентификатор IDO не может быть пустым."
                                })

    amount = serializers.FloatField(
                            required=True,
                            error_messages={
                                'blank': "Сумма не может быть пустой."
                                })

    def validate(self, attrs):
        if attrs['amount'] <= 0:
            raise ManuallyChargeError('Сумма начисления должна быть положительной')

        try:
            print(attrs['ido'])
            ido = IDO.objects.get(id=attrs['ido'])
        except Exception:
            raise IDOExistsError('Такого IDO не существует.')

        return attrs['amount'], ido
