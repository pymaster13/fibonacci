from django.contrib.auth import get_user_model
from rest_framework.status import (HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN,
                                   HTTP_200_OK, HTTP_204_NO_CONTENT,
                                   HTTP_201_CREATED)
from rest_framework.generics import (CreateAPIView, RetrieveAPIView,
                                     UpdateAPIView, DestroyAPIView,
                                     ListAPIView)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import IDO, UserOutOrder, ManuallyCharge
from .serializers import (IDOSerializer, UserOutOrderSerializer,
                          ManuallyCharge)
from .services import process_ido_data

User = get_user_model()


class IDORetrieveView(RetrieveAPIView):
    """API endpoint for retrieving IDOs."""

    queryset = IDO.objects.all()
    serializer_class = IDOSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'pk'


class IDOListView(ListAPIView):
    """API endpoint for showing all IDOs."""

    queryset = IDO.objects.all()
    serializer_class = IDOSerializer
    permission_classes = (IsAuthenticated,)


class IDOCreateView(CreateAPIView):
    """API endpoint for creating IDO."""

    queryset = IDO.objects.all()
    serializer_class = IDOSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request):
        user = User.objects.get(email=request.user)
        if user.has_perm('ido.add_ido') or user.is_superuser:

            data = process_ido_data(request.data)

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data,
                            status=HTTP_201_CREATED,
                            headers=headers)
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
            data = process_ido_data(request.data)
            serializer = self.get_serializer(
                instance,
                data=data,
                partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            if getattr(instance, '_prefetched_objects_cache', None):
                instance._prefetched_objects_cache = {}

            return Response(serializer.data)

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
