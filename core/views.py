from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Max
from rest_framework.status import (HTTP_400_BAD_REQUEST,
                                   HTTP_200_OK)
from rest_framework.generics import (GenericAPIView)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.models import Address
from ido.models import IDO, IDOParticipant, QueueUser
from .exceptions import MetamaskWalletExistsError
from .models import MetamaskWallet, AdminWallet, Coin, Transaction
from .serializers import (CustomTokenSerializer, MetamaskWalletSerializer, UserReserveSerializer)
from .services import get_main_wallet, referal_by_income


User = get_user_model()


class AddMetamaskWalletView(GenericAPIView):
    """API endpoint for adding metamask to account."""

    serializer_class = MetamaskWalletSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except MetamaskWalletExistsError as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=request.user)
            wallet_address = serializer.validated_data['wallet_address']

            address = Address.objects.create(address=wallet_address)

            try:
                existed_metamask = MetamaskWallet.objects.get(user=user)
            except Exception:
                MetamaskWallet.objects.create(user=user,
                                              wallet_address=address)
                return Response({'status': 'binded'})
            else:
                if not user.is_superuser:
                    return Response(
                        {"error": 'Изменять адрес кошелька может только администратор.'},
                        status=HTTP_400_BAD_REQUEST)
                old_address = existed_metamask.wallet_address
                existed_metamask.wallet_address = address
                existed_metamask.save()
                old_address.delete()
                return Response({'status': 'changed'})

        except Exception as e:
            print(e)
            return Response({"error": 'Ошибка привязки адреса кошелька.'},
                            status=HTTP_400_BAD_REQUEST)


class RetrieveMetamaskWalletView(GenericAPIView):
    """API endpoint for retrieving metamask to account."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            user = User.objects.get(email=request.user)
            metamask, _ = MetamaskWallet.objects.get(user=user)
            wallet_address = metamask.wallet_address.address
            return Response({'wallet_address': wallet_address})

        except Exception as e:
            print(e)
            return Response({"error": 'Ошибка получения адреса кошелька.'},
                            status=HTTP_400_BAD_REQUEST)


class RetrieveAdminWalletView(GenericAPIView):
    """API endpoint for retrieving admin wallet address."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            admin_wallet = get_main_wallet()
            return Response({'wallet_address': admin_wallet.wallet_address.address})

        except Exception as e:
            print(e)
            return Response({"error": 'Ошибка получения адреса кошелька главного аккаунта.'},
                            status=HTTP_400_BAD_REQUEST)


class FillUserReserveView(GenericAPIView):
    """API endpoint for filling user reserve (BUSD)."""

    serializer_class = UserReserveSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except MetamaskWalletExistsError as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=request.user)
            try:
                user_metamask = MetamaskWallet.objects.get(user=user)
                wallet_address_from = user_metamask.wallet_address
            except Exception:
                return Response(
                    {'error': 'У пользователя не привязан кошелек Metamask.'},
                    status=HTTP_400_BAD_REQUEST)
            try:
                admin_wallet = get_main_wallet()
            except Exception:
                return Response(
                    {'error': 'Не существует кошелька главного аккаунта.'},
                    status=HTTP_400_BAD_REQUEST)

            coin, _ = Coin.objects.get_or_create(name='BUSD', network='BEP20')
            amount = Decimal(serializer.validated_data['amount'])

            transaction = Transaction.objects.create(
                address_from=wallet_address_from,
                address_to=admin_wallet.wallet_address,
                coin=coin,
                amount=amount,
                fill_up=True
                )

            user.balance += transaction.amount
            user.save()


            admin_wallet.balance += transaction.amount
            admin_wallet.save()

            return Response({'status': 'success'})

        except Exception as e:
            print(e)
            return Response({"error": 'Ошибка пополнения резерва аккаунта.'},
                            status=HTTP_400_BAD_REQUEST)


class TakeOffUserReserveView(GenericAPIView):
    """API endpoint to takeoff user reserve (BUSD)."""

    serializer_class = UserReserveSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except MetamaskWalletExistsError as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=request.user)

            try:
                admin_wallet = get_main_wallet()
            except Exception:
                return Response(
                    {'error': 'Не существует кошелька главного аккаунта.'},
                    status=HTTP_400_BAD_REQUEST)

            try:
                user_metamask = MetamaskWallet.objects.get(user=user)
                wallet_address_to = user_metamask.wallet_address
            except Exception:
                return Response(
                    {'error': 'У пользователя не привязан кошелек Metamask.'},
                    status=HTTP_400_BAD_REQUEST)

            coin, _ = Coin.objects.get_or_create(name='BUSD', network='BEP20')
            amount = Decimal(serializer.validated_data['amount'])
            commission = Decimal(1.0)

            if user.hold:
                if user.balance < user.hold + amount + commission:
                    return Response(
                    {'error': 'У пользователя не достаточно средств для снятия из-за заморозки.'},
                    status=HTTP_400_BAD_REQUEST)

            if user.balance < amount + commission or user.balance == commission:
                return Response(
                    {'error': 'У пользователя не достаточно средств для снятия.'},
                    status=HTTP_400_BAD_REQUEST)

            if admin_wallet.balance < amount + commission:
                return Response(
                    {'error': 'На кошельке главного аккаунта не достаточно средств.'},
                    status=HTTP_400_BAD_REQUEST)

            transaction = Transaction.objects.create(
                address_from=admin_wallet.wallet_address,
                address_to=wallet_address_to,
                coin=coin,
                amount=amount-commission,
                received=True
                )

            transaction2 = Transaction.objects.create(
                address_from=user_metamask.wallet_address,
                address_to=admin_wallet.wallet_address,
                coin=coin,
                amount=commission,
                commission=True
                )

            user.balance = user.balance - transaction.amount - transaction2.amount
            user.save()
            admin_wallet.balance = admin_wallet.balance - transaction.amount + transaction2.amount
            admin_wallet.save()

            return Response({'status': 'success'})

        except Exception as e:
            print(e)
            return Response({"error": 'Ошибка снятия средств с резерва аккаунта.'},
                            status=HTTP_400_BAD_REQUEST)


class FillUserReserveByReferalsView(GenericAPIView):
    """API endpoint for filling user reserve (BUSD) by referal balance."""

    serializer_class = UserReserveSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            data = serializer.validated_data

            user = User.objects.get(email=request.user)

            if data['amount'] > user.referal_balance:
                return Response({"error": 'Недостаточно реферальных средств.'},
                                status=HTTP_400_BAD_REQUEST)

            user.referal_balance -= Decimal(data['amount'])
            user.balance += Decimal(data['amount'])
            user.save()

            return Response({'status': 'success'})

        except Exception as e:
            print(e)
            return Response({"error": 'Ошибка пополнения резерва аккаунта.'},
                            status=HTTP_400_BAD_REQUEST)


class TakeOffUserReferalsView(GenericAPIView):
    """API endpoint to takeoff user referal reserve (BUSD)."""

    serializer_class = UserReserveSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except MetamaskWalletExistsError as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=request.user)

            try:
                admin_wallet = get_main_wallet()
            except Exception:
                return Response(
                    {'error': 'Не существует кошелька главного аккаунта.'},
                    status=HTTP_400_BAD_REQUEST)

            try:
                user_metamask = MetamaskWallet.objects.get(user=user)
                wallet_address_to = user_metamask.wallet_address
            except Exception:
                return Response(
                    {'error': 'У пользователя не привязан кошелек Metamask.'},
                    status=HTTP_400_BAD_REQUEST)

            coin, _ = Coin.objects.get_or_create(name='BUSD', network='BEP20')
            amount = Decimal(serializer.validated_data['amount'])
            commission = Decimal(1.0)

            if user.referal_balance < amount + commission or user.referal_balance == commission:
                return Response(
                    {'error': 'У пользователя не достаточно средств для снятия.'},
                    status=HTTP_400_BAD_REQUEST)

            if admin_wallet.balance < amount + commission:
                return Response(
                    {'error': 'На кошельке главного аккаунта не достаточно средств.'},
                    status=HTTP_400_BAD_REQUEST)

            transaction = Transaction.objects.create(
                address_from=admin_wallet.wallet_address,
                address_to=wallet_address_to,
                coin=coin,
                amount=amount-commission,
                received=True
                )

            transaction2 = Transaction.objects.create(
                address_from=wallet_address_to,
                address_to=admin_wallet.wallet_address,
                coin=coin,
                amount=commission,
                commission=True
                )

            user.referal_balance = user.referal_balance - transaction.amount - transaction2.amount
            user.save()
            admin_wallet.balance = admin_wallet.balance - transaction.amount + transaction2.amount
            admin_wallet.save()

            return Response({'status': 'success'})

        except Exception as e:
            print(e)
            return Response({"error": 'Ошибка снятия реферальных средств с резерва аккаунта.'},
                            status=HTTP_400_BAD_REQUEST)


class TryTakeOffIDOTokensView(GenericAPIView):
    """API endpoint for try takeoff IDO user tokens from admin wallet."""

    serializer_class = CustomTokenSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        coin_name = serializer.validated_data['coin']
        if coin_name == 'BUSD':
            return Response({"error": "BUSD нельзя снять данным образом."},
                            status=HTTP_400_BAD_REQUEST)
        try:
            coin = Coin.objects.get(name=coin_name)
        except Exception:
            return Response({"error": "Такой монеты не существует."},
                            status=HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=request.user)
            try:
                metamask = MetamaskWallet.objects.get(user=user)
            except Exception as e:
                return Response({"error": "У пользователя не привязан метамаск-кошелек."},
                                status=HTTP_400_BAD_REQUEST)
            transactions = Transaction.objects.filter(address_to=metamask.wallet_address,
                                                      coin=coin,
                                                      received=False)
            if transactions:
                ido = IDO.objects.get(coin=coin)
                ido_participant = IDOParticipant.objects.get(user=user, ido=ido)

                admin_address = Address.objects.get(coin=coin, owner_admin=True)
                admin_wallet = AdminWallet.objects.get(wallet_address=admin_address)

                income_in_busd = sum(trans.amount for trans in transactions) * coin.cost_in_busd
                income_tokens = sum(trans.amount for trans in transactions)

                if ido_participant.refund_allocation < 650:
                    if Decimal(ido_participant.refund_allocation) + income_in_busd >= 650:
                        diff_busd = Decimal(ido_participant.refund_allocation) + income_in_busd - Decimal(650)
                        diff_tokens = diff_busd / coin.cost_in_busd

                        ido_participant.refund_allocation = 650
                        ido_participant.save()

                        diff_result = referal_by_income(user,
                                                        admin_wallet,
                                                        ido.smartcontract,
                                                        diff_tokens)
                        tokens_result = income_tokens - diff_tokens + diff_result

                        Transaction.objects.create(address_from=ido.smartcontract,
                                                   address_to=metamask.wallet_address,
                                                   coin=coin,
                                                   amount=tokens_result,
                                                   )
                        for trans in transactions:
                            trans.received = True
                            trans.visible = False
                            trans.save()

                        return Response({'error': 'Перерасчет заработка c IDO с учетом реферальной программы.'},
                                        status=HTTP_400_BAD_REQUEST)

                    else:
                        return Response({'status': 'success'})

                else:
                    return Response({'status': 'success'})

            return Response({"error": 'Отсутствуют транзакции.'},
                            status=HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({"error": 'Ошибка привязки адреса кошелька.'},
                            status=HTTP_400_BAD_REQUEST)



class TakeOffIDOTokensSuccessView(GenericAPIView):
    """API endpoint if takeoff IDO user tokens from admin wallet is success."""

    serializer_class = CustomTokenSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        coin_name = serializer.validated_data['coin']
        if coin_name == 'BUSD':
            return Response({"error": "BUSD нельзя снять данным образом."},
                            status=HTTP_400_BAD_REQUEST)
        try:
            coin = Coin.objects.get(name=coin_name)
        except Exception:
            return Response({"error": "Такой монеты не существует."},
                            status=HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=request.user)
            try:
                metamask = MetamaskWallet.objects.get(user=user)
            except Exception as e:
                return Response({"error": "У пользователя не привязан метамаск-кошелек."},
                                status=HTTP_400_BAD_REQUEST)
            transactions = Transaction.objects.filter(address_to=metamask.wallet_address,
                                                      coin=coin,
                                                      received=False)
            if transactions:
                ido = IDO.objects.get(coin=coin)
                ido_participant = IDOParticipant.objects.get(user=user, ido=ido)

                admin_address = Address.objects.get(coin=coin, owner_admin=True)
                admin_wallet = AdminWallet.objects.get(wallet_address=admin_address)

                income_in_busd = sum(trans.amount for trans in transactions) * coin.cost_in_busd
                income_tokens = sum(trans.amount for trans in transactions)

                for trans in transactions:
                    trans.received = True
                    trans.save()

                ido_participant.refund_allocation += float(income_in_busd)
                if ido_participant.refund_allocation > 650:
                    ido_participant.refund_allocation = 650
                ido_participant.save()

                admin_wallet.balance -= income_tokens
                admin_wallet.save()

                return Response({'status': 'success'})

            return Response({"error": 'Отсутствуют транзакции.'},
                            status=HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({"error": 'Ошибка привязки адреса кошелька.'},
                            status=HTTP_400_BAD_REQUEST)

