from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework import serializers

from account.exceptions import (EmailValidationError, LoginUserError,
                                UserDoesNotExists)
from account.serializers import EmailSerializer

User = get_user_model()


class LoginAdminSerializer(serializers.Serializer):
    """Serializer for admin authentication."""

    email = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Введите электронную почту.",
                            'required': "Поле электронной почты отсутствует.",
                            })
    password = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Введите пароль.",
                            'required': "Поле с паролем пользователя отсутствует.",
                            })
    code = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Код не может быть пустым."
                            })

    def validate(self, attrs):
        try:
            validate_email(attrs['email'])
        except ValidationError:
            raise EmailValidationError('Введите корректный почтовый ящик.')
        else:
            admin = authenticate(**attrs)
            if admin and admin.is_active and admin.is_superuser:
                return admin, attrs['code']

            raise LoginUserError(
                "Проверьте корректность введенных данных."
                )


class PermissionsSerializer(serializers.Serializer):
    """Serializer for users permissions."""

    email = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Введите электронную почту.",
                            'required': "Поле электронной почты отсутствует.",
                            })
    permissions = serializers.ListField(
                        child=serializers.CharField(),
                        required=True,
                        error_messages={
                            'blank': "Список прав не может быть пустым.",
                            'required': "Поле со списком прав отсутствует.",
                            })

    def validate(self, attrs):
        try:
            validate_email(attrs['email'])
        except ValidationError:
            raise EmailValidationError('Введите корректный почтовый ящик.')
        try:
            user = User.objects.get(email=attrs['email'])
        except Exception:
            raise UserDoesNotExists(
                "Пользователя с таким почтовым ящиком не существует."
                )
        return user, attrs['permissions']


class AddVIPUserSerializer(EmailSerializer):
    """Serializer for adding VIP user."""

    profit = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Процент не может быть пустым."
                            })


class UserPrioritySerializer(EmailSerializer):
    """Serializer for setting user queue number."""

    number = serializers.IntegerField(required=False)


class AdminCustomTokenWalletSerializer(EmailSerializer):
    """Serializer for creating admin wallet with custom tokens."""

    smartcontract = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Смартконтракт не может быть пустым."
                            })
    wallet_address = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Адрес не может быть пустым."
                            })
    decimal = serializers.FloatField(
                        required=True,
                        error_messages={
                            'blank': "Множитель не может быть пустым."
                            })
