from decimal import Decimal
from time import sleep

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
from core.exceptions import AdminWalletIsEmptyError

from core.models import AdminWallet, Coin, MetamaskWallet, Transaction, Address
from core.services import distribute_tokens, referal_by_income

from .exceptions import ExchangeAddError, IDOExistsError, AllocationError, ManuallyChargeError
from .models import IDO, IDOParticipant, QueueUser
from .serializers import (ChargeManuallySerializer, IDOSerializer, AddUserQueueSerializer,
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
                            participate_ido(user, ido, allocation, wo_pay=True)
                    else:
                        for user_ in users:
                            participate_ido(user_, ido, ido.person_allocation, wo_pay=True)
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
                        existed_user.delete()

                ex_users = [ex_user.user for ex_user in existed_users]

                if allocations:
                    for user, allocation in zip(users, allocations):
                        if user not in ex_users:
                            participate_ido(user, instance, allocation, wo_pay=True)
                else:
                    for user_ in users:
                        participate_ido(user_, instance,
                                        instance.person_allocation,
                                        wo_pay=True)

            else:
                for part in IDOParticipant.objects.filter(ido=instance):
                    part.user.hold += part.allocation
                    part.user.balance += Decimal(1.3 * part.allocation)
                    part.user.save()
                    takeoff_admin_wallet(part.allocation * Decimal(0.3))
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
            participants = IDOParticipant.objects.filter(ido=instance)
            if instance.without_pay:
                for part in participants:
                    part.delete()
            else:
                for part in participants:
                    part.user.hold += Decimal(part.allocation)
                    part.user.balance += Decimal(part.allocation)
                    part.user.save()
                    part.delete()
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
        except IDOExistsError as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)

        user = User.objects.get(email=request.user)

        ido = serializer.validated_data

        if user.balance < 651 or float(user.balance) < 1.3 * float(ido.person_allocation) + 1.0:
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

        if ido.general_allocation - used_allocation >= ido.person_allocation:
            try:
                participate_ido(user, ido, ido.person_allocation)
                referal = count_referal_hold(user, ido.person_allocation)
            except Exception as e:
                print(e)
                return Response(
                    {'error': 'Ошибка при попытке участия в данном IDO.'},
                    status=HTTP_400_BAD_REQUEST
                )

            else:
                if float(referal): 
                    if user.inviter:
                        realize_ido_part_referal(user, referal)
                        diff = Decimal(ido.person_allocation) * Decimal(0.3) - referal
                        fill_admin_wallet(user, diff)
                    else:
                        fill_admin_wallet(user, Decimal(ido.person_allocation) * Decimal(0.3))

                return Response({'status': 'success'})

        else:
            return Response(
                    {'error': 'К сожалению, вся аллокация IDO уже распределена.'},
                    status=HTTP_400_BAD_REQUEST
                )

        # except Exception as e:
        #     return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)


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


class ChargeTokensManuallyView(GenericAPIView):
    """API endpoint to manually charging tokens to IDO users."""

    serializer_class = ChargeManuallySerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):

        user = User.objects.get(email=request.user)

        if not user.has_perm('ido.add_ido'):
            if not user.is_superuser:
                return Response(
                    {'error': 'У пользователя нет прав на осуществление начисления.'},
                    status=HTTP_400_BAD_REQUEST
                )

        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except (ManuallyChargeError, IDOExistsError) as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)

        try:
            busd_amount, ido = serializer.validated_data
            amount = Decimal(busd_amount)/ido.coin.cost_in_busd

            if not ido.smartcontract:
                return Response(
                    {'error': 'Смартконтракт IDO не указан.'},
                    status=HTTP_400_BAD_REQUEST
                    )
            if not ido.charge_manually:
                return Response(
                    {'error': 'Средства в данном IDO распределяются автоматически.'},
                    status=HTTP_400_BAD_REQUEST
                    )

            address = Address.objects.get(coin=ido.coin,
                                          owner_admin=True)

            admin_wallet = AdminWallet.objects.get(wallet_address=address)

            ido_participants = IDOParticipant.objects.filter(ido=ido)
            if ido_participants:
                for part in ido_participants:
                        amount_user = referal_by_income(
                            user=part.user,
                            admin_wallet=admin_wallet,
                            smartcontract=ido.smartcontract,
                            tokens=amount)

                        part_metamask = MetamaskWallet.objects.get(user=part.user)

                        Transaction.objects.create(
                            address_from=ido.smartcontract,
                            address_to=part_metamask.wallet_address,
                            coin=admin_wallet.wallet_address.coin,
                            amount=amount_user
                            )

            return Response({'status': 'success'})

        except Exception as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)


class ChargeRefundAllocationView(GenericAPIView):
    """API endpoint to manually charging refund allocation to IDO users."""

    serializer_class = ChargeManuallySerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):

        user = User.objects.get(email=request.user)

        if not user.has_perm('ido.add_ido'):
            if not user.is_superuser:
                return Response(
                    {'error': 'У пользователя нет прав на осуществление начисления.'},
                    status=HTTP_400_BAD_REQUEST
                )

        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except (ManuallyChargeError, IDOExistsError) as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)

        try:
            amount, ido = serializer.validated_data

            ido_participants = IDOParticipant.objects.filter(ido=ido)
            if ido_participants:
                for part in ido_participants:
                    if part.refund_allocation < 650:
                        if part.refund_allocation + amount > 650:
                            part.refund_allocation = 650
                        else:
                            part.refund_allocation += amount
                        part.save()
            return Response({'status': 'success'})

        except Exception as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
