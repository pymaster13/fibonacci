from django.urls import path

from .views import (NewsRetrieveView, NewsUpdateView,
                    NewsDeleteView, NewsCreateView,
                    NewsListView)


urlpatterns = [
    path('create/', NewsCreateView.as_view(), name='create_news'),
    path('<int:pk>/', NewsRetrieveView.as_view(), name='retrieve_news'),
    path('update/<int:pk>/', NewsUpdateView.as_view(), name='update_news'),
    path('delete/<int:pk>/', NewsDeleteView.as_view(), name='delete_news'),
    path('', NewsListView.as_view(), name='list_news'),
]
