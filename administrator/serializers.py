import datetime
import re

from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework import serializers

from account.exceptions import (EmailValidationError, LoginUserError,
                                UserDoesNotExists)
from account.serializers import EmailSerializer
from administrator.exceptions import IncorrectDateError

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


class AdminCustomTokenWalletSerializer(serializers.Serializer):
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


class ReportDaySerializer(serializers.Serializer):
    """Serializer for day of report."""

    date_in_str = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Дата не может быть пустой."
                            })

    def validate(self, attrs):
        date_in_str = attrs['date_in_str']
        result = re.match(r'\d{1,2}-\d{1,2}-\d{4}', date_in_str)
        if not result:
            raise IncorrectDateError('Дата должна быть в формате dd-mm-YYYY.')

        group = result.group(0)
        splitted_group = group.split('-')
        day = splitted_group[0]
        month = splitted_group[1]
        year = splitted_group[2]

        return day, month, year


class ReportRangeDaysSerializer(serializers.Serializer):
    """Serializer for range days of report."""

    date_in_str_from = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Дата не может быть пустой."
                            })
    date_in_str_to = serializers.CharField(
                        required=True,
                        error_messages={
                            'blank': "Дата не может быть пустой."
                            })

    def validate(self, attrs):
        date_in_str_from = attrs['date_in_str_from']
        date_in_str_to = attrs['date_in_str_to']
        result1 = re.match(r'\d{1,2}-\d{1,2}-\d{4}', date_in_str_from)
        result2 = re.match(r'\d{1,2}-\d{1,2}-\d{4}', date_in_str_to)
        if not result1 or not result2:
            raise IncorrectDateError('Даты должна быть в формате dd-mm-YYYY.')

        group1 = result1.group(0)
        splitted_group1 = group1.split('-')
        day_from = splitted_group1[0]
        month_from = splitted_group1[1]
        year_from = splitted_group1[2]

        group2 = result2.group(0)
        splitted_group2 = group2.split('-')
        day_to = splitted_group2[0]
        month_to = splitted_group2[1]
        year_to = splitted_group2[2]

        
        date_from = datetime.datetime.strptime(f'{day_from}{month_from}{year_from}', "%d%m%Y").date()
        date_to = datetime.datetime.strptime(f'{day_to}{month_to}{year_to}', "%d%m%Y").date()

        if date_from >= date_to:
            raise IncorrectDateError('Указан некорректный диапазон дат.')

        return day_from, month_from, year_from, day_to, month_to, year_to