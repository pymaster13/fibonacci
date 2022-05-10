from django.contrib.auth import get_user_model
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.status import (HTTP_400_BAD_REQUEST,
                                   HTTP_200_OK)
from knox.models import AuthToken

from account.exceptions import (LoginUserError, EmailValidationError,
                                UserDoesNotExists)
from account.models import GoogleAuth
from account.serializers import EmailSerializer
from account.services import verify_google_code
from .exceptions import GrantPermissionsError
from .models import VIPUser
from .serializers import (PermissionsSerializer, LoginAdminSerializer,
                          AddVIPUserSerializer, UserPrioritySerializer)
from .services import grant_permissions


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

        except Exception:
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


class SetUserPriorityView(GenericAPIView):
    """API endpoint to set user priority."""

    serializer_class = UserPrioritySerializer
    permission_classes = (IsAdminUser,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except (EmailValidationError, UserDoesNotExists) as e:
            return Response({"error": str(e)})

        user = User.objects.get(email=serializer.validated_data['email'])
        user.priority = serializer.validated_data.get('priority', 0)
        user.save()

        return Response({'status': 'success'})
