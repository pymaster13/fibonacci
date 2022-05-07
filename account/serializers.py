from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework import serializers
from rest_framework.authtoken.models import Token as ResetPasswordToken

from .exceptions import (EmailValidationError, LoginUserError,
                         TgAccountVerifyError, InviterUserError,
                         UserWithTgExistsError, UserDoesNotExists,
                         TokenDoesNotExists)

from .models import TgAccount


User = get_user_model()


class ResetPasswordTokenSerializer(serializers.Serializer):
    """Serializer for checking token during change endpoint."""

    token = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Токен не может быть пустым.",
                            'required': "Отсутствует поле с токеном."
                            })

    def validate_token(self, token):
        try:
            token = ResetPasswordToken.objects.get(key=token)
        except Exception:
            raise TokenDoesNotExists(
                'Несуществующая ссылка для восстановления пароля.'
                )
        return token


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""

    email = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Электронная почта не может быть пустой.",
                            'required': "Поле электронной почты отсутствует.",
                            })
    password = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Пароль не может быть пустым.",
                            'required': "Отсутствует поле с паролем."
                            })

    def validate(self, attrs):
        try:
            validate_email(attrs['email'])
        except ValidationError:
            raise EmailValidationError('Введите корректную электронную почту.')
        return attrs


class TgAccountSerializer(serializers.Serializer):
    """Serializer for user authentication."""

    tg_nickname = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Телеграм-аккаунт не может быть пустым."
                            })


class TgAccountCodeSerializer(serializers.Serializer):
    """Serializer for user authentication."""

    tg_nickname = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Введите телеграм-аккаунт.",
                            'required': "Отсутствует поле телеграм-аккаунта."
                            })
    code = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Введите код подтверждения.",
                            'required': "Отсутствует поле с кодом подтверждения."
                            })


class RegisterUserSerializer(serializers.Serializer):
    """Serializer for register of user."""

    email = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Введите электронную почту.",
                            'required': "Поле электронной почты отсутствует.",
                            })
    tg_nickname = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Введите телеграм-аккаунт.",
                            'required': "Поле телеграм-аккаунта отсутствует.",
                            })
    first_name = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Введите имя пользователя.",
                            'required': "Поле с именем пользователя отсутствует.",
                            })
    last_name = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Введите фамилию пользователя.",
                            'required': "Поле с фамилией пользователя отсутствует.",
                            })
    password = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Введите пароль.",
                            'required': "Поле с паролем пользователя отсутствует.",
                            })
    inviter = serializers.CharField(required=False)

    def validate(self, attrs):
        try:
            validate_email(attrs['email'])
        except ValidationError:
            raise EmailValidationError('Введите корректную электронную почту.')

        try:
            user = User.objects.get(email=attrs['email'])
        except Exception:
            user = None

        if user:
            raise EmailValidationError(
                'Пользователь с такой электронной почтой уже существует.'
                )

        try:
            tg_account = TgAccount.objects.get(tg_nickname=attrs['tg_nickname'])
        except Exception:
            raise TgAccountVerifyError('Подтвердите телеграм-аккаунт.')

        if not tg_account.is_confirmed:
            raise TgAccountVerifyError('Подтвердите телеграм-аккаунт.')

        try:
            user = User.objects.get(telegram=tg_account)
        except Exception:
            user = None

        if user:
            raise UserWithTgExistsError(
                'Пользователь с таким телеграм-аккаунтом уже существует.'
                )

        if attrs.get('inviter', None):
            try:
                inviter = User.objects.get(invite_code=attrs['inviter'])
            except Exception:
                raise InviterUserError('Владельца инвайт-кода не существует.')
            if not inviter.can_invite:
                raise InviterUserError(
                    'Владелец инвайт-кода не может приглашать других пользователей.')

        return attrs

    def create(self, validated_data):
        user = User(email=validated_data['email'],
                    first_name=validated_data['first_name'],
                    last_name=validated_data['last_name'])

        tg_account = TgAccount.objects.get(
                        tg_nickname=validated_data['tg_nickname']
                        )
        user.telegram = tg_account

        if validated_data.get('inviter'):
            inviter = User.objects.get(invite_code=validated_data['inviter'])
            user.inviter = inviter

        user.set_password(validated_data['password'])
        user.is_active = True
        user.save()
        return user


class LoginUserSerializer(serializers.Serializer):
    """Serializer for user authentication."""

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

    def validate(self, attrs):
        try:
            validate_email(attrs['email'])
        except ValidationError:
            raise EmailValidationError('Введите корректный почтовый ящик.')
        else:
            user = authenticate(**attrs)
            if user and user.is_active:
                return user

            raise LoginUserError(
                "Проверьте корректность введенных данных."
                )


class EmailSerializer(serializers.Serializer):
    """Serializer for reseting user password."""

    email = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Введите электронную почту.",
                            'required': "Поле электронной почты отсутствует.",
                            })

    def validate_email(self, email):
        try:
            validate_email(email)
        except ValidationError:
            raise EmailValidationError('Введите корректный почтовый ящик.')

        try:
            return User.objects.get(email=email)
        except Exception:
            raise UserDoesNotExists(
                'Пользователя с такой электронной почтой не существует.'
                )


class GoogleCodeSerializer(serializers.Serializer):
    """Serializer for Google Authenticator code."""

    code = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Код не может быть пустым."
                            })


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