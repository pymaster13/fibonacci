import datetime
from math import ceil

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token as ResetPasswordToken
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.status import (HTTP_400_BAD_REQUEST,
                                   HTTP_200_OK,
                                   HTTP_403_FORBIDDEN)
from knox.models import AuthToken
import pyotp

from core.models import MetamaskWallet, Transaction
from ido.serializers import PureIDOSerializer

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
from ido.models import IDOParticipant
from core.models import Coin


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
        data = serializer.data

        data['telegram'] = {}
        data['telegram']['is_confirmed'] = user.telegram.is_confirmed
        data['telegram']['nickname'] = user.telegram.tg_nickname

        data['inviter'] = {}
        data['inviter']['id'] = user.inviter.id
        data['inviter']['email'] = user.inviter.email
        data['inviter']['telegram'] = user.inviter.telegram.tg_nickname

        return Response(data, status=HTTP_200_OK)


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


class DashboardView(GenericAPIView):
    """API endpoint to show dashboard."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = User.objects.get(email=request.user)
        idos = IDOParticipant.objects.filter(user=user)
        if idos:
            idos_allocation = sum([ido.allocation for ido in idos if ido.allocation])
        else:
            idos_allocation = 0

        try:
            metamask = MetamaskWallet.objects.get(user=user)
            user_address = metamask.wallet_address
            busd, _ = Coin.objects.get_or_create(name='BUSD')
            transactions = Transaction.objects.filter(address_to=user_address,
                                                      coin=busd,
                                                      referal=True)
            if transactions:
                referal_income = sum(trans.amount for trans in transactions if trans.amount)
            else:
                referal_income = 0

            current_year = datetime.date.today().year
            query_month_pred_2 = datetime.date.today().month - 2
            if query_month_pred_2 == -1:
                query_month_pred_2 = 11
                query_year_pred_2 = current_year - 1
                query_month_pred_1 = 12
                query_year_pred_1 = current_year - 1
            if query_month_pred_2 == 0:
                query_month_pred_2 = 12
                query_year_pred_2 = current_year - 1
                query_month_pred_1 = 1
                query_year_pred_1 = current_year
            else:
                query_year_pred_2 = current_year
                query_month_pred_1 = query_month_pred_2 + 1
                query_year_pred_1 = current_year

            transactions_m_2 = Transaction.objects.filter(address_to=user_address,
                                                          coin=busd,
                                                          referal=True,
                                                          date__month=query_month_pred_2,
                                                          date__year=query_year_pred_2)
            transactions_m_1 = Transaction.objects.filter(address_to=user_address,
                                                          coin=busd,
                                                          referal=True,
                                                          date__month=query_month_pred_1,
                                                          date__year=query_year_pred_1)
            transactions_m = Transaction.objects.filter(address_to=user_address,
                                                          coin=busd,
                                                          referal=True,
                                                          date__month=datetime.date.today().month,
                                                          date__year=datetime.date.today().year)
            referal_income_pred_2m = sum(trans.amount for trans in transactions_m_2 if trans.amount)
            referal_income_pred_m = sum(trans.amount for trans in transactions_m_1 if trans.amount)
            referal_income_current_m = sum(trans.amount for trans in transactions_m if trans.amount)

        except Exception as e:
            print(e)
            referal_income = 0
            referal_income_pred_2m = 0
            referal_income_pred_m = 0
            referal_income_current_m = 0

        result = {}

        result['invite_code'] = user.invite_code
        result['can_invite'] = user.can_invite
        result['partners_stats'] = user.partners['stats']
        result['idos_allocation'] = idos_allocation
        result['referal_balance'] = user.referal_balance
        result['referal_income'] = referal_income
        result['referal_income_current_m'] = referal_income_current_m
        result['referal_income_pred_m'] = referal_income_pred_m
        result['referal_income_pred_2m'] = referal_income_pred_2m

        if not result:
            return Response({"error": "Ошибка получения информации о пользователе."},
                            status=HTTP_400_BAD_REQUEST
                            )

        return Response(result)


class DashboardReferalChargesView(GenericAPIView):
    """API endpoint to show dashboard referal charges."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = User.objects.get(email=request.user)
        transacts = []
        try:
            metamask = MetamaskWallet.objects.get(user=user)
            user_address = metamask.wallet_address
            transactions = Transaction.objects.filter(address_to=user_address,
                                                      referal=True).order_by('date')
            if transactions:
                for trans in transactions:
                    transacts.append({'coin': trans.coin.name,
                                 'date': f'{trans.date.day}.{trans.date.month}.{trans.date.year}'
                    })

        except Exception as e:
            print(e)
            return Response({"error": "Ошибка получения информации о пользователе."},
                            status=HTTP_400_BAD_REQUEST)

        return Response({'transactions': transacts})


class UserIDOsView(GenericAPIView):
    """API endpoint to show user IDOs."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):

        user = User.objects.get(email=request.user)
        if not user.can_invite:
            return Response({
                "error": 'У пользователя нет прав на просмотр IDO.'
                }, status=HTTP_403_FORBIDDEN)
        
        result = []
        
        try:
            idos = IDOParticipant.objects.filter(user=user)
            if idos:
                for ido in idos:
                    ido_info = PureIDOSerializer(ido.ido)
                    result.append({'ido_info': ido_info.data,
                                  'user_allocation': ido.allocation})

        except Exception as e:
            print(e)
            return Response({"error": "Ошибка получения информации об IDO пользователя."},
                            status=HTTP_400_BAD_REQUEST)

        return Response({'user_idos': result})


class UserIDOsStatsView(GenericAPIView):
    """API endpoint to show user IDOs."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = User.objects.get(email=request.user)
        if not user.can_invite:
            return Response({
                "error": 'У пользователя нет прав на получение статистики.'
                }, status=HTTP_403_FORBIDDEN)
        try:
            metamask = MetamaskWallet.objects.get(user=user)
            user_address = metamask.wallet_address
        except Exception:
            Response({"error": "У пользователя не привязан кошелек Metamask."},
                     status=HTTP_400_BAD_REQUEST)
        result = []
        try:
            idos = IDOParticipant.objects.filter(user=user)
            if idos:
                for ido_part in idos:
                    coin = ido_part.ido.coin
                    smart = ido_part.ido.smartcontract

                    refund = ido_part.refund_allocation
                    ts = Transaction.objects.filter(address_to=user_address,
                                                    coin=coin)
                    if ts:
                        if ts.filter(received=True):
                            received = sum(t.amount for t in ts.filter(received=True,
                                                                       visible=True))
                        else:
                            received = 0
                        if ts.filter(received=False):
                            available = sum(t.amount for t in ts.filter(received=False,
                                                                        visible=True))
                        else:
                            available = 0
                    else:
                        received = 0
                        available = 0

                    result.append({
                        'coin': coin.name,
                        'smartcontract': smart.address if smart else '',
                        'received': received,
                        'refund_allocation': refund,
                        'available': available
                    })

        except Exception as e:
            print(e)
            return Response({"error": "Ошибка получения информации об IDO пользователя."},
                            status=HTTP_400_BAD_REQUEST)

        return Response({'idos_stats': result})


class UserPartnersStatsView(GenericAPIView):
    """API endpoint to show user partners."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = User.objects.get(email=request.user)
        if not user.can_invite:
            if not user.is_superuser:
                return Response({
                    "error": 'У пользователя нет прав на получение статистики.'
                    }, status=HTTP_403_FORBIDDEN)

        partners = user.partners['partners']
        if partners:
            return Response(partners)
        else:
            return Response({"result": "У пользователя нет партнеров."})


class PartnersStatsByEmailView(GenericAPIView):
    """API endpoint to show partners of partner."""

    serializer_class = EmailSerializer
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        request_user = User.objects.get(email=request.user)

        if not request_user.can_invite:
            return Response({
                "error": 'У пользователя нет прав на получение статистики.'
                }, status=HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid()
        except (EmailValidationError, UserDoesNotExists) as e:
            return Response({
                "error": str(e)
                }, status=HTTP_400_BAD_REQUEST)
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)

        partners = user.partners['partners']
        if partners:
            return Response(partners)
        else:
            return Response({"result": "У пользователя нет партнеров."})


class ReferalChargesView(GenericAPIView):
    """API endpoint to show refaral charges of user."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = User.objects.get(email=request.user)

        if not user.can_invite:
            return Response({
                "error": 'У пользователя нет прав на получение статистики.'
                }, status=HTTP_403_FORBIDDEN)

        try:
            metamask = MetamaskWallet.objects.get(user=user)
            user_address = metamask.wallet_address
        except Exception:
            Response({"error": "У пользователя не привязан кошелек Metamask."},
                     status=HTTP_400_BAD_REQUEST)

        result = []
        transactions = Transaction.objects.filter(address_to=user_address,
                                                  referal=True)
        if transactions:
            for ts in transactions:
                wallet_from = MetamaskWallet.objects.get(wallet_address=ts.address_from) 
                result.append({
                    'date': f'{ts.date.day}.{ts.date.month}.{ts.date.year}',
                    'coin': ts.coin.name,
                    'amount': ts.amount,
                    'from': wallet_from.user.email,
                })

        return Response({"referal_charges": result})
