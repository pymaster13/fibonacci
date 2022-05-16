from datetime import datetime
from logging import exception
from re import X
from django.contrib.auth import get_user_model
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (HTTP_400_BAD_REQUEST,
                                   HTTP_403_FORBIDDEN,
                                   HTTP_200_OK)
from knox.models import AuthToken

from account.exceptions import (LoginUserError, EmailValidationError, RetrievePermissionsError,
                                UserDoesNotExists)
from account.models import GoogleAuth
from account.serializers import EmailSerializer
from account.services import paginate, retrieve_permissions, verify_google_code
from .exceptions import GrantPermissionsError, IncorrectDateError
from .models import VIPUser
from .serializers import (PermissionsSerializer, LoginAdminSerializer,
                          AddVIPUserSerializer, ReportDaySerializer, ReportRangeDaysSerializer, UserPrioritySerializer,
                          AdminCustomTokenWalletSerializer)
from .services import (grant_permissions, refresh_queue_places,
                       retrieve_users_info)
from ido.models import IDOParticipant, QueueUser
from core.models import Address, AdminWallet, Coin, MetamaskWallet, Transaction


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
            if not user.permanent_place:
                return Response(
                    {"error": 'Пользователь не состоит в приоритетной очереди.'},
                    status=HTTP_400_BAD_REQUEST
                )

            users = User.objects.filter(permanent_place__gt=user.permanent_place)
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
        new_admin_address = Address.objects.create(
            address=data['wallet_address'],
            coin=smrt.coin,
            owner_admin=True
        )

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

        user = User.objects.get(email=request.user)
        if user.has_perm('statistics.add_statistics') or user.is_superuser:
            try:
                participants = IDOParticipant.objects.all()
                IDO_investment = sum(part.allocation for part in participants if part.allocation)
                users = User.objects.all()
                count_users = len(users)
                count_users_pool = 0
                for user_ in users:
                    if user_.balance >= 651:
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
                status=HTTP_403_FORBIDDEN)


class AdminStatsAKVIncomeView(GenericAPIView):
    """API endpoint to retrive akv incomes by months."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):

        user = User.objects.get(email=request.user)
        if user.has_perm('statistics.add_statistics') or user.is_superuser:
            current_year = datetime.now().year
            months = range(1, 13)
            months_slug = ('Январь', 'Февраль', 'Март', 'Апрель',
                           'Май', 'Июнь', 'Июль', 'Август',
                           'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь')

            coin = Coin.objects.get(name='BUSD')

            result = {}

            for index, month in enumerate(months):
                transactions = Transaction.objects.filter(coin=coin,
                                                          commission=True,
                                                          date__month=month,
                                                          date__year=current_year)
                akv_income_by_day = sum(t.amount for t in transactions if t.amount)

                result[months_slug[index]] = akv_income_by_day

            return Response(result)
        else:
            return Response({
                "error": 'У пользователя нет прав на получение статистики.'},
                status=HTTP_403_FORBIDDEN)


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

            coin = Coin.objects.get(name='BUSD')
            admin_address = Address.objects.get(coin=coin, owner_admin=True)
            fill_busd_transactions = Transaction.objects.filter(address_to=admin_address,
                                                                coin=coin,
                                                                fill_up=True,
                                                                date__day=day,
                                                                date__month=month,
                                                                date__year=year)
            fill_reserve_by_day = sum(t.amount for t in fill_busd_transactions if t.amount)

            takeoff_busd_transactions = Transaction.objects.filter(address_from=admin_address,
                                                                   coin=coin,
                                                                   received=True,
                                                                   date__day=day,
                                                                   date__month=month,
                                                                   date__year=year)
            takeoff_reserve_by_day = sum(t.amount for t in takeoff_busd_transactions if t.amount)

            referals_transactions = Transaction.objects.filter(coin=coin,
                                                         referal=True,
                                                         date__day=day,
                                                         date__month=month,
                                                         date__year=year)
            referals_by_day = sum(t.amount for t in referals_transactions if t.amount)
            transactions_with_commission = Transaction.objects.filter(coin=coin,
                                                                      commission=True,
                                                                      date__day=day,
                                                                      date__month=month,
                                                                      date__year=year)
            akv_income_by_day = sum(t.amount for t in transactions_with_commission if t.amount)

            return Response({'fill_reserve': fill_reserve_by_day,
                             'takeoff_reserve': takeoff_reserve_by_day,
                             'referals': referals_by_day,
                             'akv_income': akv_income_by_day,
                            })
        else:
            return Response({
                "error": 'У пользователя нет прав на получение статистики.'},
                status=HTTP_403_FORBIDDEN)


class AdminReportByRangeDaysView(GenericAPIView):
    """API endpoint to retrive report statistics by range days."""

    serializer_class = ReportRangeDaysSerializer
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

            day_from, month_from, year_from, day_to, month_to, year_to  = serializer.validated_data
            date_from = f'{year_from}-{month_from}-{day_from}'
            date_to = f'{year_to}-{month_to}-{day_to}'

            coin = Coin.objects.get(name='BUSD')
            admin_address = Address.objects.get(coin=coin, owner_admin=True)
            fill_busd_transactions = Transaction.objects.filter(address_to=admin_address,
                                                                coin=coin,
                                                                fill_up=True,
                                                                date__range=[date_from, date_to])
            fill_reserve_by_day = sum(t.amount for t in fill_busd_transactions if t.amount)

            takeoff_busd_transactions = Transaction.objects.filter(address_from=admin_address,
                                                                   coin=coin,
                                                                   received=True,
                                                                   date__range=[date_from, date_to])
            takeoff_reserve_by_day = sum(t.amount for t in takeoff_busd_transactions if t.amount)

            referals_transactions = Transaction.objects.filter(coin=coin,
                                                         referal=True,
                                                         date__range=[date_from, date_to])
            referals_by_day = sum(t.amount for t in referals_transactions if t.amount)
            transactions_with_commission = Transaction.objects.filter(coin=coin,
                                                                      commission=True,
                                                                      date__range=[date_from, date_to])
            akv_income_by_day = sum(t.amount for t in transactions_with_commission if t.amount)

            return Response({'fill_reserve': fill_reserve_by_day,
                             'takeoff_reserve': takeoff_reserve_by_day,
                             'referals': referals_by_day,
                             'akv_income': akv_income_by_day,
                            })
        else:
            return Response({
                "error": 'У пользователя нет прав на получение статистики.'},
                status=HTTP_403_FORBIDDEN)


class AdminStatsByClickUserView(GenericAPIView):
    """API endpoint to show stats about user by click."""

    serializer_class = EmailSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):

        user = User.objects.get(email=request.user)
        if not user.has_perm('user.add_user'):
            if not user.is_superuser:
                return Response({
                    "error": 'У пользователя нет прав на получение информации о пользователях.'},
                    status=HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except (EmailValidationError, UserDoesNotExists) as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)

        user = User.objects.get(email=serializer.validated_data['email'])
        try:
            metamask_user = MetamaskWallet.objects.get(user=user)
        except Exception:
            return Response({'error': 'У пользователя не привязан кошелек.'}, status=HTTP_400_BAD_REQUEST)

        result = []

        try:
            idos = IDOParticipant.objects.filter(user=user)
            if idos:
                for ido_part in idos:
                    coin = ido_part.ido.coin
                    allocation = ido_part.allocation
                    refund_allocation = ido_part.refund_allocation
                    ts = Transaction.objects.filter(address_to=metamask_user.wallet_address,
                                                    coin=coin)
                    amount_in_tokens = sum(t.amount for t in ts if t.amount)
                    if coin.cost_in_busd:
                        amount_in_busd = amount_in_tokens * coin.cost_in_busd
                    else:
                        amount_in_busd = 0

                    income_from_income = ido_part.income_from_income


                    result.append({
                        'coin': coin.name,
                        'allocation': allocation,
                        'refund_allocation': refund_allocation,
                        'amount_in_busd': amount_in_busd,
                        'income_from_income': income_from_income
                    })

        except Exception as e:
            print(e)
            return Response({"error": "Ошибка получения информации об IDO пользователя."},
                            status=HTTP_400_BAD_REQUEST)

        return Response({'idos_stats': result})


class RetrieveAllUsersPermissions(GenericAPIView):
    """API endpoint to retrieve info about users permissions."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):

        user = User.objects.get(email=request.user)
        if not user.has_perm('user.add_user'):
            if not user.is_superuser:
                return Response({
                    "error": 'У пользователя нет прав на получение информации о пользователях.'},
                    status=HTTP_403_FORBIDDEN)

        result = []

        users = User.objects.all().order_by('email')
        for user in users:
            try:
                permissions = retrieve_permissions(user)
            except RetrievePermissionsError as e:
                return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)
            else:
                if permissions:
                    result.append({user.email: permissions})

        result, count_pages, current_page = paginate(result,
                                                     6,
                                                     int(request.data.get('page', 1)))

        return Response({'users': result,
                         'count_pages': count_pages,
                         'current_page': current_page})


class RetrieveAllVIPUsers(GenericAPIView):
    """API endpoint to retrieve info about vip-users."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):

        user = User.objects.get(email=request.user)
        if not user.has_perm('user.add_user'):
            if not user.is_superuser:
                return Response({
                    "error": 'У пользователя нет прав на получение информации о пользователях.'},
                    status=HTTP_403_FORBIDDEN)

        result = []

        vip_users = VIPUser.objects.all()
        for vip_user in vip_users:
            result.append({vip_user.user.email: vip_user.referal_profit})

        result, count_pages, current_page = paginate(result,
                                                     6,
                                                     int(request.data.get('page', 1)))

        return Response({'users': result,
                         'count_pages': count_pages,
                         'current_page': current_page})


class RetrieveAllUsersPriorities(GenericAPIView):
    """API endpoint to retrieve info about users priorities."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):

        user = User.objects.get(email=request.user)
        if not user.has_perm('user.add_user'):
            if not user.is_superuser:
                return Response({
                    "error": 'У пользователя нет прав на получение информации о пользователях.'},
                    status=HTTP_403_FORBIDDEN)

        result = []

        users = User.objects.all()
        for user in users:
            if user.permanent_place:
                result.append({user.email: user.permanent_place})

        result, count_pages, current_page = paginate(result,
                                                     6,
                                                     int(request.data.get('page', 1)))

        return Response({'users': result,
                         'count_pages': count_pages,
                         'current_page': current_page})


class UsersPartnersStatsView(GenericAPIView):
    """API endpoint to show users partners."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = User.objects.get(email=request.user)
        if not user.has_perm('user.add_user'):
            if not user.is_superuser:
                return Response({
                    "error": 'У пользователя нет прав на получение информации о пользователях.'},
                    status=HTTP_403_FORBIDDEN)

        result = []

        users = User.objects.all()
        for user in users:
            dict_user = {}
            dict_user['info'] = user.as_json()
            dict_user['stats'] = user.partners['stats']
            result.append(dict_user)

        result, count_pages, current_page = paginate(
                                                result,
                                                10,
                                                int(request.data.get('page', 1))
                                            )

        return Response({'users': result,
                         'count_pages': count_pages,
                         'current_page': current_page})
