from django.contrib.auth import get_user_model
from rest_framework.status import (HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN,
                                   HTTP_200_OK, HTTP_204_NO_CONTENT,
                                   HTTP_201_CREATED)
from rest_framework.generics import (CreateAPIView, RetrieveAPIView,
                                     UpdateAPIView, DestroyAPIView,
                                     ListAPIView, GenericAPIView)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .exceptions import ExchangeAddError, IDOExistsError, AllocationError
from .models import IDO, IDOParticipant, ManuallyCharge
from .serializers import (IDOSerializer,
                          ManuallyCharge, ParticipateIDOSerializer, PureIDOSerializer)
from .services import process_ido_data

User = get_user_model()


class IDORetrieveView(RetrieveAPIView):
    """API endpoint for retrieving IDOs."""

    queryset = IDO.objects.all()
    serializer_class = PureIDOSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'pk'


class IDOListView(ListAPIView):
    """API endpoint for showing all IDOs."""

    queryset = IDO.objects.all()
    serializer_class = PureIDOSerializer
    permission_classes = (IsAuthenticated,)


class IDOCreateView(CreateAPIView):
    """API endpoint for creating IDO."""

    queryset = IDO.objects.all()
    serializer_class = IDOSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request):
        user = User.objects.get(email=request.user)
        if user.has_perm('ido.add_ido') or user.is_superuser:

            try:
                data, users = process_ido_data(request.data)
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=HTTP_400_BAD_REQUEST)

            serializer = PureIDOSerializer(data=data)
            serializer.is_valid(raise_exception=True)

            ido = IDO.objects.create(**serializer.validated_data)

            if users and serializer.validated_data['without_pay']:
                for u in users:
                    try:
                        IDOParticipant.objects.create(user=u,
                                                      ido=ido)
                    except Exception:
                        return Response(
                            {'error': 'Один из пользователей уже в очереди данного IDO.'},
                            status=HTTP_400_BAD_REQUEST
                        )
            return Response(serializer.data,
                            status=HTTP_201_CREATED)
        return Response({
                "error": 'У пользователя нет прав на создание IDO.'
                }, status=HTTP_403_FORBIDDEN)


class IDOUpdateView(UpdateAPIView):
    """API endpoint for updating IDO."""

    permission_classes = (IsAuthenticated,)
    queryset = IDO.objects.all()
    serializer_class = IDOSerializer
    lookup_field = 'pk'

    def update(self, request, **kwargs):
        user = User.objects.get(email=request.user)
        if user.has_perm('ido.change_ido') or user.is_superuser:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()

            try:
                data, users = process_ido_data(request.data)
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=HTTP_400_BAD_REQUEST)

            serializer = PureIDOSerializer(
                instance,
                data=data,
                partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            if getattr(instance, '_prefetched_objects_cache', None):
                instance._prefetched_objects_cache = {}

            if instance.without_pay:
                existed_users = IDOParticipant.objects.filter(
                                            ido=instance
                                            )
                for existed_user in existed_users:
                    if existed_user.user not in users:
                        existed_user.delete()

                for u in users:
                    user, _ = IDOParticipant.objects.get_or_create(
                                                      user=u,
                                                      ido=instance)
            return Response(serializer.data,
                            status=HTTP_200_OK)

        return Response({
                "error": 'У пользователя нет прав на изменение IDO.'
                }, status=HTTP_403_FORBIDDEN)


class IDODeleteView(DestroyAPIView):
    """API endpoint for deleting IDO."""

    permission_classes = (IsAuthenticated,)
    queryset = IDO.objects.all()
    serializer_class = IDOSerializer
    lookup_field = 'pk'

    def destroy(self, request, *args, **kwargs):
        user = User.objects.get(email=request.user)
        if user.has_perm('ido.delete_ido') or user.is_superuser:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=HTTP_204_NO_CONTENT)

        return Response({
                "error": 'У пользователя нет прав на удаление IDO.'
                }, status=HTTP_403_FORBIDDEN)


class ParticipateIDOView(GenericAPIView):
    """API endpoint to participate in IDO by user."""

    serializer_class = ParticipateIDOSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)

            user = User.objects.get(email=request.user)

            if user.balance < 651:
                return Response(
                    {'error': 'У пользователя недостаточно средств на счете.'},
                    status=HTTP_400_BAD_REQUEST
                    )

            ido, allocation = serializer.validated_data

            if ido.without_pay:
                return Response(
                    {'error': 'Очередь для данного IDO назначается вручную.'},
                    status=HTTP_400_BAD_REQUEST
                    )

            try:
                IDOParticipant.objects.create(user=user,
                                              ido=ido,
                                              allocation=allocation)
            except Exception:
                return Response(
                    {'error': 'Пользователь уже в очереди данного IDO.'},
                    status=HTTP_400_BAD_REQUEST
                    )
            else:
                return Response({'status': 'success'})

        except Exception as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
