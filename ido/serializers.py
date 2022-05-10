from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework import serializers

from .exceptions import IDOExistsError, AllocationError
from .models import IDO, ManuallyCharge
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

    class Meta:
        model = IDO
        fields = '__all__'


class ManuallyChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManuallyCharge
        fields = '__all__'


class ParticipateIDOSerializer(serializers.Serializer):

    ido = serializers.IntegerField(
                    required=True,
                    error_messages={
                        'blank': "IDO не может быть пустым."
                        })
    allocation = serializers.FloatField(required=False)

    def validate(self, attrs):
        try:
            ido = IDO.objects.get(pk=attrs['ido'])
        except Exception:
            raise IDOExistsError('Указан некорректный идентификатор IDO.')

        if attrs.get('allocation', 0) < 0:
            raise AllocationError('Аллокация не может быть отрицательной.')

        return ido, attrs.get('allocation', None)
