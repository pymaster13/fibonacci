from django.contrib.auth import get_user_model
from rest_framework.status import (HTTP_400_BAD_REQUEST,
                                   HTTP_200_OK)
from rest_framework.generics import (GenericAPIView)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from knox.models import AuthToken

from .exceptions import (LoginUserError, EmailValidationError,
                         TgAccountVerifyError, InviterUserError,
                         UserWithTgExistsError,)
from .models import TgAccount, TgCode
from .serializers import (RegisterUserSerializer, LoginUserSerializer,
                          TgAccountSerializer, TgAccountCodeSerializer)
from .services import generate_code, check_code_time


User = get_user_model()


class ConfirmTgAccountView(GenericAPIView):
    """API endpoint for confirming of telegram account."""

    serializer_class = TgAccountCodeSerializer
    permission_classes = (AllowAny,)

    def post(self, request):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            tg_nick = serializer.validated_data['tg_nickname']
            code = serializer.validated_data['code']
            tg_account = TgAccount.objects.get(
                                    tg_nickname=tg_nick
                                    )

            if tg_account.is_confirmed:
                return Response({"error": 'Телеграм-аккаунт уже подтвержден.'},
                                status=HTTP_400_BAD_REQUEST)

            tg_code = TgCode.objects.get(tg_account=tg_account)

            if tg_code.code == code:
                if check_code_time(tg_code, 20):
                    tg_account.is_confirmed = True
                    tg_account.save()

                    return Response({
                        "tg_nickname": tg_account.tg_nickname,
                        "confirmed": True},
                        status=HTTP_200_OK)
                else:
                    return Response({
                        "error": 'Код подтверждения истек.'
                        }, status=HTTP_400_BAD_REQUEST)

            return Response({
                "error": 'Неверный код подтверждения.'
                }, status=HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(e)
            return Response({"error": 'Ошибка подтверждения аккаунта.'},
                            status=HTTP_400_BAD_REQUEST)


class GetTgCodeView(GenericAPIView):
    """API endpoint for checking of telegram account."""

    serializer_class = TgAccountSerializer
    permission_classes = (AllowAny,)

    def post(self, request):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            tg_nick = serializer.validated_data['tg_nickname']
            tg_account, acc_created = TgAccount.objects.get_or_create(
                                    tg_nickname=tg_nick
                                    )

            if acc_created:
                tg_code = generate_code(tg_account)
                return Response({
                    "tg_nickname": tg_account.tg_nickname,
                    "code": tg_code.code},
                    status=HTTP_200_OK)

            if tg_account.is_confirmed:
                return Response({"error": 'Телеграм-аккаунт уже подтвержден.'},
                                status=HTTP_400_BAD_REQUEST)

            tg_code = TgCode.objects.get(tg_account=tg_account)

            if not check_code_time(tg_code, 20):
                tg_code.delete()
                new_tg_code = generate_code(tg_account)
                return Response({
                    "tg_nickname": tg_account.tg_nickname,
                    "code": new_tg_code.code},
                    status=HTTP_200_OK)

            return Response({
                "error": 'Высланный код еще действителен.'
                }, status=HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(e)
            return Response({"error": 'Ошибка во время получения кода.'},
                            status=HTTP_400_BAD_REQUEST)


class RegisterUserView(GenericAPIView):
    """API endpoint for creation of user."""

    serializer_class = RegisterUserSerializer

    def post(self, request):

        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except (EmailValidationError, TgAccountVerifyError,
                InviterUserError, UserWithTgExistsError) as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)

        user = serializer.save()

        return Response({
            "id": user.id,
            "email": user.email,
            "tg_nickname": user.telegram.tg_nickname,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "token": AuthToken.objects.create(user)[1]
        })


class LoginUserView(GenericAPIView):
    """API endpoint for user authentication."""

    serializer_class = LoginUserSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except LoginUserError as e:
            print(e)
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)

        user = serializer.validated_data
        return Response({
            "id": user.id,
            "email": user.email,
            "token": AuthToken.objects.create(user)[1]
        })
