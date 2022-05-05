import email
from django.contrib.auth import get_user_model
from rest_framework.status import (HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN,
                                   HTTP_200_OK, HTTP_204_NO_CONTENT,
                                   HTTP_201_CREATED)
from rest_framework.generics import (CreateAPIView, RetrieveAPIView,
                                     UpdateAPIView, DestroyAPIView,
                                     ListAPIView)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import News
from .serializers import NewsDetailSerializer


User = get_user_model()


class NewsRetrieveView(RetrieveAPIView):
    """API endpoint for retrieving news."""

    queryset = News.objects.all()
    serializer_class = NewsDetailSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'pk'


class NewsListView(ListAPIView):
    """API endpoint for showing all news."""

    queryset = News.objects.all()
    serializer_class = NewsDetailSerializer
    permission_classes = (IsAuthenticated,)


class NewsCreateView(CreateAPIView):
    """API endpoint for creating news."""

    queryset = News.objects.all()
    serializer_class = NewsDetailSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request):
        user = User.objects.get(email=request.user)
        if user.has_perm('news.add_news') or user.is_superuser:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data,
                            status=HTTP_201_CREATED,
                            headers=headers)
        return Response({
                "error": 'У пользователя нет прав на создание новостей.'
                }, status=HTTP_403_FORBIDDEN)


class NewsUpdateView(UpdateAPIView):
    """API endpoint for updating news."""

    permission_classes = (IsAuthenticated,)
    queryset = News.objects.all()
    serializer_class = NewsDetailSerializer
    lookup_field = 'pk'

    def update(self, request, **kwargs):
        user = User.objects.get(email=request.user)
        if user.has_perm('news.change_news') or user.is_superuser:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(
                instance,
                data=request.data,
                partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            if getattr(instance, '_prefetched_objects_cache', None):
                instance._prefetched_objects_cache = {}

            return Response(serializer.data)

        return Response({
                "error": 'У пользователя нет прав на изменение новостей.'
                }, status=HTTP_403_FORBIDDEN)


class NewsDeleteView(DestroyAPIView):
    """API endpoint for deleting news."""

    permission_classes = (IsAuthenticated,)
    queryset = News.objects.all()
    serializer_class = NewsDetailSerializer
    lookup_field = 'pk'

    def destroy(self, request, *args, **kwargs):
        user = User.objects.get(email=request.user)
        if user.has_perm('news.delete_news') or user.is_superuser:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=HTTP_204_NO_CONTENT)

        return Response({
                "error": 'У пользователя нет прав на удаление новостей.'
                }, status=HTTP_403_FORBIDDEN)
