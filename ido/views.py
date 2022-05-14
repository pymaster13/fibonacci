from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Max
from rest_framework.status import (HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN,
                                   HTTP_200_OK, HTTP_204_NO_CONTENT,
                                   HTTP_201_CREATED)
from rest_framework.generics import (CreateAPIView, RetrieveAPIView,
                                     UpdateAPIView, DestroyAPIView,
                                     ListAPIView, GenericAPIView)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import AdminWallet, Coin, MetamaskWallet, Transaction

from .exceptions import ExchangeAddError, IDOExistsError, AllocationError
from .models import IDO, IDOParticipant, QueueUser
from .serializers import (IDOSerializer, AddUserQueueSerializer,
                          ParticipateIDOSerializer, PureIDOSerializer)
from .services import (decline_ido_part_referal, delete_participant, process_ido_data, fill_admin_wallet,
                       realize_ido_part_referal, participate_ido, takeoff_admin_wallet,
                       count_referal_hold)

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
                data, users, allocations = process_ido_data(request.data)
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=HTTP_400_BAD_REQUEST)

            serializer = PureIDOSerializer(data=data)
            serializer.is_valid(raise_exception=True)

            ido = IDO.objects.create(**serializer.validated_data)

            if users and not serializer.validated_data['without_pay']:
                ido.delete()
                return Response(
                            {'error': 'Поле "Без оплаты" неактивно.'},
                            status=HTTP_400_BAD_REQUEST
                        )

            if users and serializer.validated_data['without_pay']:
                try:
                    if allocations:
                        if sum(allocations) > ido.general_allocation:
                            ido.delete()
                            return Response(
                                {'error': 'Аллокация пользователей превышает аллокацию проекта.'},
                                status=HTTP_400_BAD_REQUEST
                            )

                        for user, allocation in zip(users, allocations):
                            referal = count_referal_hold(user, allocation)
                            participate_ido(user, ido, allocation)
                            fill_admin_wallet(int(allocation * 0.3))
                            if referal and user.inviter:
                                realize_ido_part_referal(user, referal)
                    else:
                        for user_ in users:
                            referal = count_referal_hold(user, ido.person_allocation)
                            participate_ido(user_, ido, ido.person_allocation)
                            fill_admin_wallet(int(ido.person_allocation * 0.3))
                            if referal and user_.inviter:
                                realize_ido_part_referal(user_, referal)
                except Exception as e:
                    print(e)
                    ido.delete()
                    return Response(
                        {'error': str(e)},
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
                data, users, allocations = process_ido_data(request.data)
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=HTTP_400_BAD_REQUEST)

            if sum(allocations) > instance.general_allocation:
                return Response(
                    {'error': 'Аллокация пользователей превышает аллокацию проекта.'},
                    status=HTTP_400_BAD_REQUEST
                )

            serializer = PureIDOSerializer(instance,
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
                        existed_user.user.hold += existed_user.allocation
                        existed_user.user.balance += 1.3 * existed_user.allocation
                        existed_user.user.save()
                        takeoff_admin_wallet(int(existed_user.allocation * 0.3))
                        existed_user.delete()

                ex_users = [ex_user.user for ex_user in existed_users]

                print(111)

                if allocations:
                    for user, allocation in zip(users, allocations):
                        if user not in ex_users:
                            referal = count_referal_hold(user, allocation)
                            participate_ido(user, instance, allocation, True)
                            fill_admin_wallet(int(allocation * 0.3))
                            if referal and user.inviter:
                                realize_ido_part_referal(user, referal)
                else:
                    for user_ in users:
                        referal = count_referal_hold(user_,
                                                     instance.person_allocation)
                        participate_ido(user_, instance,
                                        instance.person_allocation,
                                        True)
                        fill_admin_wallet(int(instance.person_allocation * 0.3))
                        if referal and user_.inviter:
                            realize_ido_part_referal(user_, referal)

            else:
                for part in IDOParticipant.objects.filter(ido=instance):
                    part.user.hold += part.allocation
                    part.user.balance += 1.3 * part.allocation
                    part.user.save()
                    takeoff_admin_wallet(int(part.allocation * 0.3))
                    part.delete()

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

            for part in IDOParticipant.objects.filter(ido=instance):
                part.user.hold += part.allocation
                part.user.save()
                part.delete()
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

            ido = serializer.validated_data

            if user.balance < 651 or user.balance < Decimal(1.3) * Decimal(ido.person_allocation) + Decimal(1):
                return Response(
                    {'error': 'У пользователя недостаточно средств на счете.'},
                    status=HTTP_400_BAD_REQUEST
                    )

            try:
                queue_object = QueueUser.objects.get(ido=ido, user=user)
                if queue_object.number > ido.count_participants:
                    return Response(
                        {'error': 'Место в очереди не позволяет Вам участововать в данном IDO.'},
                        status=HTTP_400_BAD_REQUEST
                    )
            except Exception:
                return Response(
                        {'error': 'Вы не находитесь в очереди на участие в IDO.'},
                        status=HTTP_400_BAD_REQUEST
                    )

            participants = IDOParticipant.objects.filter(ido=ido)
            used_allocation = len(participants) * ido.person_allocation

            referal = count_referal_hold(user, ido.person_allocation)

            if ido.general_allocation - used_allocation >= ido.person_allocation:
                try:
                    participate_ido(user, ido, ido.person_allocation)

                except Exception as e:
                    print(e)
                    return Response(
                        {'error': 'Вы уже участвуете в данном IDO.'},
                        status=HTTP_400_BAD_REQUEST
                    )

                else:
                    fill_admin_wallet(int(ido.person_allocation * 0.3))

                    if referal and user.inviter:
                        realize_ido_part_referal(user, referal)

                    return Response({'status': 'success'})

            else:
                return Response(
                        {'error': 'К сожалению, вся аллокация IDO уже распределена.'},
                        status=HTTP_400_BAD_REQUEST
                    )

        except Exception as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)


class AddUserQueue(GenericAPIView):
    """API endpoint to add user to IDO queue."""

    serializer_class = AddUserQueueSerializer
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

            ido = serializer.validated_data

            if ido.without_pay:
                return Response(
                    {'error': 'Очередь для данного IDO назначается вручную.'},
                    status=HTTP_400_BAD_REQUEST
                    )

            try:
                QueueUser.objects.get(user=user, ido=ido)
                return Response(
                    {'error': 'Пользователь уже в очереди данного IDO.'},
                    status=HTTP_400_BAD_REQUEST
                    )
            except:
                pass

            if user.permanent_place:
                permanent = True
                number = user.permanent_place
            else:
                permanent = False
                all_queues = QueueUser.objects.filter(ido=ido)
                if not all_queues:
                    number = 1
                else:
                    number = all_queues.aggregate(Max('number'))['number__max'] + 1

            try:
                queues = QueueUser.objects.filter(ido=ido, number__gte=number)
                if queues:
                    for q in queues:
                        q.number += 1
                        q.save()
                QueueUser.objects.create(user=user,
                                         ido=ido,
                                         permanent=permanent,
                                         number=number)

            except Exception as e:
                print(e)
                return Response(
                    {'error': 'Ошибка при добавлении пользователя в очередь IDO.'},
                    status=HTTP_400_BAD_REQUEST
                    )
            else:
                return Response({'status': 'success'})

        except Exception as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
