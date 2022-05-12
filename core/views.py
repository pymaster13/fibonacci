from django.contrib.auth import get_user_model
from django.db.models import Max
from rest_framework.status import (HTTP_400_BAD_REQUEST,
                                   HTTP_200_OK)
from rest_framework.generics import (GenericAPIView)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.models import Address
from ido.models import QueueUser
from .exceptions import MetamaskWalletExistsError
from .models import MetamaskWallet, AdminWallet, Coin, Transaction
from .serializers import (MetamaskWalletSerializer, UserReserveSerializer)


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
            admin_wallet = AdminWallet.objects.first()
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
                admin_wallet = AdminWallet.objects.first()
            except Exception:
                return Response(
                    {'error': 'Не существует кошелька главного аккаунта.'},
                    status=HTTP_400_BAD_REQUEST)

            coin, _ = Coin.objects.get_or_create(name='BUSD', network='BEP20')
            amount = serializer.validated_data['amount']

            transaction = Transaction.objects.create(
                address_from=wallet_address_from,
                address_to=admin_wallet.wallet_address,
                coin=coin,
                amount=amount
                )

            user.balance += amount
            user.save()
            admin_wallet.balance += amount
            admin_wallet.save()

            if user.balance > 651:
                queue_object, created = QueueUser.objects.get_or_create(user=user)
                print(QueueUser.objects.get_or_create(user=user))
                print(1)
                if created:
                    print(2)
                    print(QueueUser.objects.aggregate(Max('number')))
                    max_value = QueueUser.objects.aggregate(Max('number'))
                    if not max_value:
                        queue_object.number = 1
                    else:
                        queue_object.number = max_value['number__max'] + 1
                    queue_object.permanent = False
                    queue_object.save()

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
                admin_wallet = AdminWallet.objects.first()
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
            amount = serializer.validated_data['amount']
            commission=1.0

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
                amount=amount,
                commission=commission
                )

            user.balance = user.balance - amount - commission
            user.save()
            admin_wallet.balance = admin_wallet.balance - amount + commission
            admin_wallet.save()

            return Response({'status': 'success'})

        except Exception as e:
            print(e)
            return Response({"error": 'Ошибка снятия средств с резерва аккаунта.'},
                            status=HTTP_400_BAD_REQUEST)
