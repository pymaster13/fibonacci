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
            metamask, _ = MetamaskWallet.objects.get_or_create(user=user)
            metamask.wallet_address = address
            metamask.save()

            return Response({'binded': True})

        except Exception as e:
            print(e)
            return Response({"error": 'Ошибка привязки адреса кошелька.'},
                            status=HTTP_400_BAD_REQUEST)
