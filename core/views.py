from django.contrib.auth import get_user_model
from rest_framework.status import (HTTP_400_BAD_REQUEST,
                                   HTTP_200_OK)
from rest_framework.generics import (GenericAPIView)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from knox.models import AuthToken

from core.models import Address
from .exceptions import MetamaskWalletExistsError
from .models import MetamaskWallet
from .serializers import MetamaskWalletSerializer


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
    """API endpoint for retriebing metamask to account."""

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
