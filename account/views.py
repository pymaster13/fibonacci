from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token as ResetPasswordToken
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.status import (HTTP_400_BAD_REQUEST,
                                   HTTP_200_OK)
from knox.models import AuthToken
import pyotp
from yaml import serialize

from .exceptions import (LoginUserError, EmailValidationError,
                         TgAccountVerifyError, InviterUserError,
                         UserWithTgExistsError, UserDoesNotExists,
                         TokenDoesNotExists, RetrievePermissionsError)
from .models import TgAccount, TgCode, GoogleAuth
from .serializers import (RegisterUserSerializer, LoginUserSerializer,
                          TgAccountSerializer, TgAccountCodeSerializer,
                          EmailSerializer, ChangePasswordSerializer,
                          ResetPasswordTokenSerializer, GoogleCodeSerializer,
                          UserSerializer)
from .services import (generate_code, check_code_time,
                       verify_google_code, send_mail_message,
                       generate_google_qrcode, retrieve_permissions)
from administrator.services import retrieve_users_info


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
        if user.inviter:
            user.line = user.inviter.line + 1
            user.save()

            if user.inviter.status == 'N':
                user.inviter.status = 'A'
                user.inviter.save()

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
        except (LoginUserError, EmailValidationError) as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)

        user = serializer.validated_data

        if not user.is_superuser:
            return Response({
                "id": user.id,
                "email": user.email,
                "token": AuthToken.objects.create(user)[1]
            })

        return Response({
                "status": "superuser"
            })


class ResetPasswordView(GenericAPIView):
    """API endpoint to reset user password."""

    serializer_class = EmailSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except (UserDoesNotExists, EmailValidationError) as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)

        user = User.objects.get(email=serializer.validated_data['email'])

        existed_tokens = ResetPasswordToken.objects.filter(user=user)
        if existed_tokens:
            existed_tokens.delete()

        token = ResetPasswordToken.objects.create(user=user)
        send_mail_message(token)

        return Response({
            "email": token.user.email,
            "token": token.key,
        })


class CheckResetTokenView(GenericAPIView):
    """API endpoint for checking user token to reset password."""

    serializer_class = ResetPasswordTokenSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenDoesNotExists as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)

        token = ResetPasswordToken.objects.get(
                    key=serializer.validated_data['token']
                    )

        email = token.user.email

        token.delete()

        return Response({'email': email}, status=HTTP_200_OK)


class ChangeUserPasswordView(GenericAPIView):
    """API endpoint for changing user password during reseting."""

    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except EmailValidationError as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)

        user = User.objects.get(email=serializer.validated_data['email'])
        user.set_password(serializer.validated_data['password'])
        user.save()

        return Response({
            "id": user.id,
            "email": user.email,
            "status": "Пароль успешно восстановлен."
        })


class GenerateGoogleQRView(GenericAPIView):
    """API endpoint for generating Google Authenticator QR-code."""

    serializer_class = EmailSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except EmailValidationError as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)

        user = User.objects.get(email=serializer.validated_data['email'])

        existed_objects = GoogleAuth.objects.filter(user=user)
        existed_objects.delete()
        token = pyotp.random_base32()

        google_auth = GoogleAuth.objects.create(user=user, token=token)
        qrcode = generate_google_qrcode(google_auth.token, user.email)
        if not qrcode:
            return Response(
                {"error": "Ошибка генерации QR-кода гугл-аутентификации."},
                status=HTTP_400_BAD_REQUEST
                )
        return Response({'qr-code': qrcode})


class VerifyGoogleCodeView(GenericAPIView):
    """API endpoint to verify Google Authenticator code."""

    serializer_class = GoogleCodeSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        user = User.objects.get(email=request.user)

        google_auth = GoogleAuth.objects.get(user=user)
        result = verify_google_code(google_auth.token,
                                    serializer.validated_data['code'])
        if not result:
            return Response({"error": "Введите корректный код."},
                            status=HTTP_400_BAD_REQUEST
                            )

        google_auth.is_installed = True
        google_auth.save()

        return Response({'status': 'success'})


class RetrievePermissionsView(GenericAPIView):
    """API endpoint to retrieve user permissions."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = User.objects.get(email=request.user)

        try:
            permissions = retrieve_permissions(user)
        except RetrievePermissionsError as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)
        else:
            return Response({'user': user.email,
                             'permissions': list(permissions)})


class RetrieveUserInfoView(GenericAPIView):
    """API endpoint to retrieve user info."""

    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request):
        user = User.objects.get(email=request.user)
        serializer = self.get_serializer(user)

        return Response(serializer.data, status=HTTP_200_OK)


class RetrieveUserPartnersView(GenericAPIView):
    """API endpoint to retrieve info about user partners."""

    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request):
        try:
            user = User.objects.get(email=request.user)
            data = retrieve_users_info([user])
            return Response({'users': data}, status=HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)
