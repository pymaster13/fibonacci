from logging import exception
from re import X
from django.contrib.auth import get_user_model
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (HTTP_400_BAD_REQUEST,
                                   HTTP_200_OK)
from knox.models import AuthToken

from account.exceptions import (LoginUserError, EmailValidationError,
                                UserDoesNotExists)
from account.models import GoogleAuth
from account.serializers import EmailSerializer
from account.services import verify_google_code
from .exceptions import GrantPermissionsError, IncorrectDateError
from .models import VIPUser
from .serializers import (PermissionsSerializer, LoginAdminSerializer,
                          AddVIPUserSerializer, ReportDaySerializer, UserPrioritySerializer,
                          AdminCustomTokenWalletSerializer)
from .services import (grant_permissions, refresh_queue_places,
                       retrieve_users_info)
from ido.models import IDOParticipant, QueueUser
from core.models import Address, AdminWallet, Coin, Transaction


User = get_user_model()


class LoginAdminUserView(GenericAPIView):
    """API endpoint for admin authentication."""

    serializer_class = LoginAdminSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except (LoginUserError, EmailValidationError) as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)

        admin, code = serializer.validated_data

        try:
            google_auth = GoogleAuth.objects.get(user=admin)
            result = verify_google_code(google_auth.token, code)
            if not result:
                return Response({"error": "Введите корректный код."},
                                status=HTTP_400_BAD_REQUEST
                                )

            google_auth.is_installed = True
            google_auth.save()

            return Response({
                "id": admin.id,
                "email": admin.email,
                "token": AuthToken.objects.create(admin)[1]
            })

        except Exception as e:
            print(e)
            return Response({"error": 'Ошибка во время авторизации.'},
                            status=HTTP_400_BAD_REQUEST)


class GrantPermissionsView(GenericAPIView):
    """API endpoint to grant permissions to user."""

    serializer_class = PermissionsSerializer
    permission_classes = (IsAdminUser,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except (EmailValidationError, UserDoesNotExists) as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)

        user, perms = serializer.validated_data

        try:
            grant_permissions(user, perms)
        except GrantPermissionsError as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)
        else:
            return Response({'user': user.email, 'status': "success"})


class AllowUserInviteView(GenericAPIView):
    """API endpoint to open interface for user."""

    serializer_class = EmailSerializer
    permission_classes = (IsAdminUser,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except (EmailValidationError, UserDoesNotExists) as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)

        user = User.objects.get(email=serializer.validated_data['email'])

        if not user.can_invite:
            user.can_invite = True
            user.save()
            return Response({'user': user.email, 'status': "success"})
        else:
            return Response({'error': 'Пользователю уже открыты все вкладки.'})


class Reset2FAView(GenericAPIView):
    """API endpoint to reset user 2FA."""

    serializer_class = EmailSerializer
    permission_classes = (IsAdminUser,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except (EmailValidationError, UserDoesNotExists) as e:
            return Response({"error": str(e)})

        user = User.objects.get(email=serializer.validated_data['email'])

        try:
            google_auth = GoogleAuth.objects.get(user=user)
            google_auth.delete()
            return Response({'user': user.email, 'status': "success"})
        except Exception as e:
            print(e)
            return Response({
                "error": 'Аккаунт не привязан к Google Authenticator.'},
                status=HTTP_400_BAD_REQUEST)


class AddVIPUserView(GenericAPIView):
    """API endpoint to create VIP user with stable referal profit."""

    serializer_class = AddVIPUserSerializer
    permission_classes = (IsAdminUser,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except (EmailValidationError, UserDoesNotExists) as e:
            return Response({"error": str(e)})

        user = User.objects.get(email=serializer.validated_data['email'])

        try:
            vip_user, _ = VIPUser.objects.get_or_create(user=user)
            vip_user.referal_profit = serializer.validated_data['profit']
            vip_user.save()
            return Response({'user': vip_user.user.email, 'status': "success"})
        except Exception as e:
            print(e)
            return Response({
                "error": 'Ошибка создания VIP-пользователя.'},
                status=HTTP_400_BAD_REQUEST)


class DeleteVIPUserView(GenericAPIView):
    """API endpoint to delete VIP user with stable referal profit."""

    serializer_class = EmailSerializer
    permission_classes = (IsAdminUser,)

    def delete(self, request):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except (EmailValidationError, UserDoesNotExists) as e:
            return Response({"error": str(e)})

        user = User.objects.get(email=serializer.validated_data['email'])

        try:
            vip_user = VIPUser.objects.get(user=user)
            vip_user.delete()
            return Response({'status': "success"})
        except Exception as e:
            print(e)
            return Response({
                "error": 'Ошибка удаления VIP-пользователя.'},
                status=HTTP_400_BAD_REQUEST)


class SetUserPermanentPlaceView(GenericAPIView):
    """API endpoint to set user priority."""

    serializer_class = UserPrioritySerializer
    permission_classes = (IsAdminUser,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except (EmailValidationError, UserDoesNotExists) as e:
            return Response({"error": str(e)})

        data = serializer.validated_data
        number = data.get('number', None)

        user = User.objects.get(email=data['email'])

        if not number:
            print(user.permanent_place)
            if not user.permanent_place:
                return Response(
                    {"error": 'Пользователь не состоит в приоритетной очереди.'},
                    status=HTTP_400_BAD_REQUEST
                )

            users = User.objects.filter(permanent_place__gt=user.permanent_place)
            print(users)
            for u in users:
                u.permanent_place -= 1
                u.save()

            user.permanent_place = None
            user.save()

            refresh_queue_places(user)

            return Response({'status': 'success'})

        if number < 1:
            return Response(
                {"error": 'Номер в очереди не может быть меньше 1.'},
                status=HTTP_400_BAD_REQUEST)

        try:
            users = User.objects.filter(permanent_place__gte=number)
            for u in users:
                u.permanent_place += 1
                u.save()

            user.permanent_place = number
            user.save()
            refresh_queue_places(user)

            return Response({'status': 'success'})

        except Exception as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)


class GetUserIDOView(GenericAPIView):
    """API endpoint to get user ido's allocation."""

    serializer_class = EmailSerializer
    permission_classes = (IsAdminUser,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except (EmailValidationError, UserDoesNotExists) as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)

        user = User.objects.get(email=serializer.validated_data['email'])

        idos = IDOParticipant.objects.filter(user=user)
        summ = sum([ido.allocation for ido in idos if ido.allocation])

        return Response({'email': user.email, 'summ': summ})


class RetrieveUsersInformationView(GenericAPIView):
    """API endpoint to get users info."""

    permission_classes = (IsAdminUser,)

    def get(self, request):
        try:
            users = User.objects.all().order_by('email')
            data = retrieve_users_info(users)
            return Response({'users': data}, status=HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)


class CreateCustomTokenWalletView(GenericAPIView):
    """API endpoint to create admin wallet with custom tokens."""

    serializer_class = AdminCustomTokenWalletSerializer
    permission_classes = (IsAdminUser,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        smrt = Address.objects.get(address=data['smartcontract'])
        print(smrt)
        new_admin_address = Address.objects.create(
            address=data['wallet_address'],
            coin=smrt.coin,
            owner_admin=True
        )
        print(new_admin_address)

        AdminWallet.objects.create(
            wallet_address=new_admin_address,
            decimal=data['decimal']
        )

        try:
            return Response({'status': "success"})
        except Exception as e:
            print(e)
            return Response({
                "error": 'Ошибка создания кошелька с токенами.'},
                status=HTTP_400_BAD_REQUEST)


class AdminStatsView(GenericAPIView):
    """API endpoint to retrive admin statistics."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):

        print(1)
        user = User.objects.get(email=request.user)
        print(2)
        if user.has_perm('statistics.add_statistics') or user.is_superuser:
            try:
                participants = IDOParticipant.objects.all()
                IDO_investment = sum(part.allocation for part in participants if part.allocation)
                users = User.objects.all()
                count_users = len(users)
                count_users_pool = 0
                for user_ in users:
                    if user_.balance > 650:
                        count_users_pool += 1
                pool = count_users_pool * 650

                queue = set()
                for q in QueueUser.objects.all():
                    queue.add(q.user)

                count_queues = len(queue)

                busd_on_admin_wallet = sum(u.balance for u in users if u.balance)
                referals_usd_on_admin_wallet = sum(u.referal_balance for u in users if u.referal_balance)

                general_balance = busd_on_admin_wallet + referals_usd_on_admin_wallet

                return Response({'investment': IDO_investment,
                                 'count_users': count_users,
                                 'pool': pool,
                                 'users_in_queues': count_queues,
                                 'balance': general_balance,
                                 'reserve': busd_on_admin_wallet
                                })

            except Exception as e:
                print(e)
                return Response({
                    "error": str(e)},
                    status=HTTP_400_BAD_REQUEST)
        else:
            return Response({
                "error": 'У пользователя нет прав на получение статистики.'},
                status=HTTP_400_BAD_REQUEST)


class AdminReportByDayView(GenericAPIView):
    """API endpoint to retrive report statistics by day."""

    serializer_class = ReportDaySerializer
    permission_classes = (IsAuthenticated,)

    def get(self, request):

        user = User.objects.get(email=request.user)
        if user.has_perm('statistics.add_statistics') or user.is_superuser:
            serializer = self.get_serializer(data=request.data)
            try:
                serializer.is_valid(raise_exception=True)
            except IncorrectDateError as e:
                return Response({"error": str(e)},
                                status=HTTP_400_BAD_REQUEST)

            day, month, year = serializer.validated_data

            print(day, month, year)

            coin = Coin.objects.get(name='BUSD')
            admin_address = Address.objects.get(coin=coin, owner_admin=True)
            # пополнено BUSD
            # выведено BUSD
            # реферальные начисления
            # доход AKV
            all_tr = Transaction.objects.all()
            for t in all_tr:
                print(t.date.day, t.date.month, t.date.year) 
            fill_busd_transactions = Transaction.objects.filter(address_to=admin_address,
                                                                coin=coin,
                                                                referal=False,
                                                                commission=0.0,
                                                                date__day=day,
                                                                date__month=month,
                                                                date__year=year)
            print(fill_busd_transactions)
            fill_reserve_by_day = sum(t.amount for t in fill_busd_transactions if t.amount)

            takeoff_busd_transactions = Transaction.objects.filter(address_from=admin_address,
                                                                   coin=coin,
                                                                   referal=False,
                                                                   date__day=day,
                                                                   date__month=month,
                                                                   date__year=year)
            print(takeoff_busd_transactions)
            takeoff_reserve_by_day = sum(t.amount for t in takeoff_busd_transactions if t.amount)

            referals_transactions = Transaction.objects.filter(coin=coin,
                                                         referal=True,
                                                         date__day=day,
                                                         date__month=month,
                                                         date__year=year)
            referals_by_day = sum(t.amount for t in referals_transactions if t.amount)
            transactions_with_commission = Transaction.objects.filter(coin=coin,
                                                                      commission__gt=0,
                                                                      date__day=day,
                                                                      date__month=month,
                                                                      date__year=year)
            print(transactions_with_commission)
            akv_income_by_day = sum(t.commission for t in transactions_with_commission if t.commission)

            return Response({'fill_reserve': fill_reserve_by_day,
                             'takeoff_reserve': takeoff_reserve_by_day,
                             'referals': referals_by_day,
                             'akv_income': akv_income_by_day,
                            })
        else:
            return Response({
                "error": 'У пользователя нет прав на получение статистики.'},
                status=HTTP_400_BAD_REQUEST)
